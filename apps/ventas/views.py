from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from decimal import Decimal
from datetime import date

from .models import Pedido, DetallePedido
from .forms import PedidoForm, TipoDocumentoForm, BoletaForm, FacturaForm
from apps.productos.models import Producto
from apps.documentos.models import DocumentoVenta, DetalleDocumento


# =========================
# LISTAR PEDIDOS
# =========================
@login_required
def listar_pedidos(request):
    """Muestra todos los pedidos con sus documentos asociados"""
    pedidos = Pedido.objects.select_related('cliente', 'usuario').prefetch_related('detalles').all().order_by('-fecha_creacion')

    # Filtros opcionales por usuario o cliente
    filtro_usuario = request.GET.get('usuario')
    filtro_cliente = request.GET.get('cliente')

    if filtro_usuario:
        pedidos = pedidos.filter(usuario__username__icontains=filtro_usuario)
    if filtro_cliente:
        pedidos = pedidos.filter(cliente__nombre__icontains=filtro_cliente)

    context = {
        'pedidos': pedidos,
    }
    return render(request, 'ventas/listar_pedidos.html', context)


# =========================
# PASO 1: CREAR PEDIDO (DATOS DEL DOCUMENTO)
# =========================
@login_required
def crear_pedido_datos(request):
    """Primera etapa: cliente, tipo de documento y datos de venta"""
    if request.method == 'POST':
        pedido_form = PedidoForm(request.POST)
        tipo_form = TipoDocumentoForm(request.POST)

        tipo_documento = request.POST.get('tipo_documento')
        
        # Determinar qué formulario usar según el tipo de documento
        if tipo_documento == 'Boleta':
            doc_form = BoletaForm(request.POST)
        elif tipo_documento == 'Factura':
            doc_form = FacturaForm(request.POST)
        else:
            doc_form = None

        if pedido_form.is_valid() and tipo_form.is_valid() and (doc_form and doc_form.is_valid()):
            # Crear el pedido (sin productos todavía)
            pedido = pedido_form.save(commit=False)
            pedido.usuario = request.user
            pedido.save()

            # ✅ AQUÍ VA EL CÓDIGO: Guardar datos del documento en sesión
            if tipo_documento == 'Boleta':
                request.session['pedido_temp_data'] = {
                    'tipo_documento': tipo_documento,
                    'medio_de_pago': doc_form.cleaned_data.get('medio_de_pago'),
                }
            else:  # Factura
                request.session['pedido_temp_data'] = {
                    'tipo_documento': tipo_documento,
                    'medio_de_pago': doc_form.cleaned_data.get('medio_de_pago'),
                    'fecha_emision': str(doc_form.cleaned_data.get('fecha_emision')),
                    'fecha_vencimiento': str(doc_form.cleaned_data.get('fecha_vencimiento')),
                    'razon_social': doc_form.cleaned_data.get('razon_social'),
                    'rut': doc_form.cleaned_data.get('rut'),
                    'giro': doc_form.cleaned_data.get('giro'),
                    'direccion': doc_form.cleaned_data.get('direccion'),
                    'ciudad': doc_form.cleaned_data.get('ciudad'),
                    'comuna': doc_form.cleaned_data.get('comuna'),
                }

            messages.success(request, f'Pedido #{pedido.id} creado. Ahora agregue productos.')
            return redirect('agregar_productos_pedido', pedido_id=pedido.id)
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:
        pedido_form = PedidoForm()
        tipo_form = TipoDocumentoForm()
        boleta_form = BoletaForm()
        factura_form = FacturaForm()

    context = {
        'pedido_form': pedido_form,
        'tipo_form': tipo_form,
        'boleta_form': boleta_form,
        'factura_form': factura_form,
    }

    return render(request, 'ventas/crear_pedido_datos.html', context)

@login_required
def agregar_productos_pedido(request, pedido_id):
    """Segunda etapa: añadir productos al pedido"""
    pedido = get_object_or_404(Pedido, id=pedido_id)
    pedido_temp = request.session.get('pedido_temp_data')

    if not pedido_temp:
        messages.error(request, 'Debe completar los datos del documento antes de agregar productos.')
        return redirect('crear_pedido_datos')

    productos = Producto.objects.filter(activo=True).order_by('nombre')
    detalles = DetallePedido.objects.filter(pedido=pedido)

    if request.method == 'POST':
        # =============================
        # Confirmar pedido y generar documento
        # =============================
        if 'confirmar_pedido' in request.POST:
            if not detalles.exists():
                messages.error(request, 'Debe agregar al menos un producto antes de confirmar.')
                return redirect('agregar_productos_pedido', pedido_id=pedido.id)

            try:
                with transaction.atomic():
                    # 🔍 Verificar stock suficiente antes de descontar
                    for detalle in detalles:
                        producto = detalle.producto
                        if detalle.cantidad > producto.stock:
                            raise ValueError(f"No hay suficiente stock de {producto.nombre} (Stock: {producto.stock})")

                    # 🔻 Descontar stock de cada producto
                    for detalle in detalles:
                        producto = detalle.producto
                        producto.stock -= detalle.cantidad
                        producto.save()

                    # 💰 Calcular totales
                    subtotal = sum(detalle.cantidad * detalle.precio_unitario_venta for detalle in detalles)
                    iva = subtotal * Decimal('0.19')  # IVA 19%
                    total = subtotal + iva

                    # 🧾 Crear documento de venta
                    tipo_documento = pedido_temp.get('tipo_documento', 'Boleta')
                    
                    documento = DocumentoVenta.objects.create(
                        pedido=pedido,
                        tipo_documento=tipo_documento,
                        cliente=pedido.cliente,
                        vendedor=request.user,
                        medio_de_pago=pedido_temp.get('medio_de_pago', ''),
                        neto=subtotal,
                        iva=iva,
                        total=total,
                        fecha_vencimiento=pedido_temp.get('fecha_vencimiento') if tipo_documento == 'Factura' else None,
                        razon_social=pedido_temp.get('razon_social', '') if tipo_documento == 'Factura' else '',
                        rut=pedido_temp.get('rut', '') if tipo_documento == 'Factura' else '',
                        giro=pedido_temp.get('giro', '') if tipo_documento == 'Factura' else '',
                        direccion=pedido_temp.get('direccion', '') if tipo_documento == 'Factura' else '',
                        ciudad=pedido_temp.get('ciudad', '') if tipo_documento == 'Factura' else '',
                        comuna=pedido_temp.get('comuna', '') if tipo_documento == 'Factura' else '',
                        estado='Pagada' if tipo_documento == 'Boleta' else 'Emitida'
                    )

                    # 📦 Crear detalles del documento
                    for detalle in detalles:
                        DetalleDocumento.objects.create(
                            documento=documento,
                            producto=detalle.producto,
                            cantidad=detalle.cantidad,
                            precio_unitario_venta=detalle.precio_unitario_venta,
                            costo_unitario_venta=detalle.producto.costo_unitario
                        )

                    # ✅ Actualizar estado del pedido
                    pedido.estado = 'Procesando'
                    pedido.save()

                    # 💾 Limpiar datos temporales de sesión
                    if 'pedido_temp_data' in request.session:
                        del request.session['pedido_temp_data']

                    messages.success(request, f'Pedido #{pedido.id} y {documento.tipo_documento} #{documento.folio} creados exitosamente.')
                    return redirect('detalle_pedido', pedido_id=pedido.id)

            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f'Error al generar el pedido: {str(e)}')
                print(e)

        # =============================
        # Agregar producto al pedido (GUARDAR EN BD)
        # =============================
        else:
            producto_id = request.POST.get('producto_id')
            cantidad = int(request.POST.get('cantidad', 1))
            producto = get_object_or_404(Producto, id=producto_id)

            if producto.stock < cantidad:
                messages.error(request, f'Stock insuficiente. Disponible: {producto.stock}')
            else:
                # ✅ Crear o actualizar DetallePedido en la base de datos
                detalle, created = DetallePedido.objects.get_or_create(
                    pedido=pedido,
                    producto=producto,
                    defaults={
                        'cantidad': cantidad,
                        'precio_unitario_venta': producto.precio_unitario,
                        'subtotal': cantidad * producto.precio_unitario
                    }
                )

                if not created:
                    # Si ya existe, sumar la cantidad
                    detalle.cantidad += cantidad
                    detalle.subtotal = detalle.cantidad * detalle.precio_unitario_venta
                    detalle.save()

                messages.success(request, f'{producto.nombre} agregado al pedido.')

            return redirect('agregar_productos_pedido', pedido_id=pedido.id)

    # Preparar carrito para mostrar en template
    carrito = []
    for detalle in detalles:
        carrito.append({
            'producto_id': detalle.producto.id,
            'nombre': detalle.producto.nombre,
            'cantidad': detalle.cantidad,
            'precio': detalle.precio_unitario_venta,
            'subtotal': detalle.subtotal,
        })

    context = {
        'pedido': pedido,
        'productos': productos,
        'carrito': carrito,
        'tipo_documento': pedido_temp.get('tipo_documento'),
    }

    return render(request, 'ventas/agregar_productos_pedido.html', context)

# =========================
# ELIMINAR PRODUCTO DEL CARRITO
# =========================
@login_required
def eliminar_producto_carrito(request, pedido_id, producto_id):
    """Elimina un producto del carrito temporal"""
    carrito = request.session.get(f'carrito_pedido_{pedido_id}', [])
    carrito = [item for item in carrito if item['producto_id'] != str(producto_id)]
    request.session[f'carrito_pedido_{pedido_id}'] = carrito
    messages.success(request, 'Producto eliminado del pedido.')
    return redirect('agregar_productos_pedido', pedido_id=pedido_id)


# =========================
# DETALLE DEL PEDIDO
# =========================
@login_required
def detalle_pedido(request, pedido_id):
    """Muestra el detalle de un pedido con sus productos y documento asociado"""
    pedido = get_object_or_404(
        Pedido.objects.select_related('cliente', 'usuario')
        .prefetch_related('detalles__producto'),
        id=pedido_id
    )
    
    # Obtener detalles del pedido
    detalles = pedido.detalles.all()
    
    # Verificar si el pedido tiene documento
    try:
        documento = DocumentoVenta.objects.get(pedido=pedido)
    except DocumentoVenta.DoesNotExist:
        documento = None

    context = {
        'pedido': pedido,
        'detalles': detalles,
        'documento': documento,
    }
    return render(request, 'ventas/detalle_pedido.html', context)

@login_required
def confirmar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)

    if pedido.estado != 'Pendiente':
        messages.warning(request, 'Este pedido ya fue confirmado o procesado.')
        return redirect('detalle_pedido', pedido_id=pedido.id)

    detalles = DetallePedido.objects.filter(pedido=pedido)

    if not detalles.exists():
        messages.error(request, 'No se puede confirmar un pedido sin productos.')
        return redirect('detalle_pedido', pedido_id=pedido.id)

    datos_doc = request.session.get('pedido_temp_data', {})

    try:
        with transaction.atomic():  # ✅ Asegura que todo se haga o nada se haga

            # 🔍 Verificar stock suficiente antes de descontar
            for detalle in detalles:
                producto = detalle.producto
                if detalle.cantidad > producto.stock:
                    raise ValueError(f"No hay suficiente stock de {producto.nombre} (Stock: {producto.stock})")

            # 🔻 Descontar stock de cada producto
            for detalle in detalles:
                producto = detalle.producto
                producto.stock -= detalle.cantidad
                producto.save()

            # 💰 Calcular totales
            subtotal = sum(detalle.cantidad * detalle.producto.precio_unitario for detalle in detalles)
            iva = subtotal * Decimal('0.19')  # IVA 19%
            total = subtotal + iva

            # 🧾 Crear documento de venta
            tipo_documento = datos_doc.get('tipo_documento', 'Boleta')
            
            documento = DocumentoVenta.objects.create(
                pedido=pedido,
                tipo_documento=tipo_documento,
                cliente=pedido.cliente,
                vendedor=request.user,
                medio_de_pago=datos_doc.get('medio_de_pago', ''),
                neto=subtotal,
                iva=iva,
                total=total,
                fecha_vencimiento=datos_doc.get('fecha_vencimiento') if tipo_documento == 'Factura' else None,
                razon_social=datos_doc.get('razon_social', '') if tipo_documento == 'Factura' else '',
                rut=datos_doc.get('rut', '') if tipo_documento == 'Factura' else '',
                giro=datos_doc.get('giro', '') if tipo_documento == 'Factura' else '',
                direccion=datos_doc.get('direccion', '') if tipo_documento == 'Factura' else '',
                ciudad=datos_doc.get('ciudad', '') if tipo_documento == 'Factura' else '',
                comuna=datos_doc.get('comuna', '') if tipo_documento == 'Factura' else '',
            )

            # 📦 Crear detalles del documento
            for detalle in detalles:
                DetalleDocumento.objects.create(
                    documento=documento,
                    producto=detalle.producto,
                    cantidad=detalle.cantidad,
                    precio_unitario_venta=detalle.producto.precio_unitario,
                    costo_unitario_venta=detalle.producto.costo_unitario
                )

            # ✅ Actualizar estado del pedido
            pedido.estado = 'Procesando'
            pedido.save()

            # 💾 Limpiar datos temporales de sesión
            if 'pedido_temp_data' in request.session:
                del request.session['pedido_temp_data']

            messages.success(request, f'El Pedido #{pedido.id} ha sido confirmado. Documento {tipo_documento} #{documento.folio} generado correctamente.')

    except ValueError as e:
        # ❌ Si algo falla, no se confirma el pedido
        messages.error(request, str(e))
    except Exception as e:
        messages.error(request, 'Ocurrió un error inesperado al confirmar el pedido.')
        print(e)  # opcional: útil para debug

    return redirect('detalle_pedido', pedido_id=pedido.id)


@login_required
def marcar_pedido_enviado(request, pedido_id):
    """Cambia el estado del pedido a 'Enviado' si está procesando."""
    pedido = get_object_or_404(Pedido, id=pedido_id)

    if pedido.estado != 'Procesando':
        messages.warning(request, 'Solo se pueden marcar como enviados los pedidos en proceso.')
        return redirect('detalle_pedido', pedido_id=pedido.id)

    pedido.estado = 'Enviado'
    pedido.save()

    messages.success(request, f'El pedido #{pedido.id} ha sido marcado como Enviado.')
    return redirect('detalle_pedido', pedido_id=pedido.id)