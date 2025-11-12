from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction, models
from decimal import Decimal
from datetime import date

from apps.ventas.models import Pedido, DetallePedido
from apps.ventas.forms import PedidoForm, TipoDocumentoForm, BoletaForm, FacturaForm
from apps.productos.models import Producto
from apps.documentos.models import DocumentoVenta, DetalleDocumento

from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from django.db.models import Sum, Count

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

        # Inicializar el formulario correcto según tipo_documento
        if tipo_documento == 'Boleta':
            doc_form = BoletaForm(request.POST)
        elif tipo_documento == 'Factura':
            doc_form = FacturaForm(request.POST)
        else:
            doc_form = None

        # Validación principal
        if pedido_form.is_valid() and tipo_form.is_valid():
            # Validar también formulario de documento si corresponde
            if tipo_documento == 'Boleta' and doc_form.is_valid():
                pedido = pedido_form.save(commit=False)
                pedido.usuario = request.user
                pedido.save()

                # Guardar datos en sesión solo para Boleta
                request.session['pedido_temp_data'] = {
                    'tipo_documento': tipo_documento,
                    'medio_de_pago': doc_form.cleaned_data.get('medio_de_pago'),
                }

                messages.success(request, f'Pedido #{pedido.id} creado. Ahora agregue productos.')
                return redirect('agregar_productos_pedido', pedido_id=pedido.id)

            elif tipo_documento == 'Factura' and doc_form.is_valid():
                pedido = pedido_form.save(commit=False)
                pedido.usuario = request.user
                pedido.save()

                # Guardar datos en sesión para Factura
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
                messages.error(request, 'Por favor complete correctamente los datos del documento seleccionado.')
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


# =========================
# PASO 2: AGREGAR PRODUCTOS AL PEDIDO
# =========================

@login_required
def agregar_productos_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)

    # Productos activos disponibles
    productos = Producto.objects.filter(activo=True).order_by('nombre')
    
    # Detalles actuales del pedido
    detalles = DetallePedido.objects.filter(pedido=pedido)

    # Generar carrito con los productos ya agregados
    carrito = [{
        'producto_id': d.producto.id,
        'nombre': d.producto.nombre,
        'cantidad': d.cantidad,
        'precio': d.precio_unitario_venta,
        'subtotal': d.subtotal
    } for d in detalles]

    # Variable para mostrar errores en el template
    mensaje_error = None

    # Obtener tipo de documento desde la sesión (si existe)
    pedido_temp = request.session.get('pedido_temp', {})
    tipo_documento = pedido_temp.get('tipo_documento', 'No especificado')

    # Procesar POST: Agregar producto
    if request.method == "POST" and "producto_id" in request.POST:
        producto_id = request.POST.get("producto_id")
        cantidad = int(request.POST.get("cantidad", 1))

        try:
            producto = get_object_or_404(Producto, id=producto_id)

            # Calcular cuántos ya tiene en el pedido
            cantidad_actual = DetallePedido.objects.filter(
                pedido=pedido, 
                producto=producto
            ).aggregate(total=models.Sum('cantidad'))['total'] or 0

            cantidad_total_solicitada = cantidad_actual + cantidad

            # Validar stock disponible
            if producto.stock < cantidad_total_solicitada:
                mensaje_error = (
                    f"⚠️ Stock insuficiente para {producto.nombre}. "
                    f"Solicitado: {cantidad_total_solicitada} | "
                    f"Disponible: {producto.stock} | "
                    f"Ya tienes {cantidad_actual} en el pedido."
                )
            else:
                # Crear detalle del pedido
                DetallePedido.objects.create(
                    pedido=pedido,
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario_venta=producto.precio_unitario
                )

                # Descontar stock
                producto.stock -= cantidad
                producto.save()

                messages.success(
                    request, 
                    f"✅ {producto.nombre} agregado correctamente al pedido #{pedido.id}."
                )
                return redirect('agregar_productos_pedido', pedido_id=pedido.id)

        except Exception as e:
            mensaje_error = f"❌ Error al agregar el producto: {str(e)}"

    # Procesar POST: Confirmar pedido
    if request.method == "POST" and "confirmar_pedido" in request.POST:
        if not detalles.exists():
            messages.warning(request, "⚠️ No puedes confirmar un pedido sin productos.")
            return redirect('agregar_productos_pedido', pedido_id=pedido.id)

        # Cambiar estado del pedido
        pedido.estado = 'Procesando'
        pedido.save()

        messages.success(request, f"✅ Pedido #{pedido.id} confirmado correctamente.")
        return redirect('detalle_pedido', pedido_id=pedido.id)

    # Contexto para el template
    context = {
        'pedido': pedido,
        'carrito': carrito,
        'productos': productos,
        'tipo_documento': tipo_documento,
        'mensaje_error': mensaje_error,
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


# =========================
# CONFIRMAR PEDIDO
# =========================
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
        with transaction.atomic():
            # 🔍 Verificar stock suficiente antes de descontar
            productos_sin_stock = []
            for detalle in detalles:
                producto = detalle.producto
                if detalle.cantidad > producto.stock:
                    productos_sin_stock.append(
                        f"{producto.nombre} (Solicitado: {detalle.cantidad}, Disponible: {producto.stock})"
                    )

            if productos_sin_stock:
                mensaje_error = "⚠️ No hay suficiente stock para los siguientes productos:\n" + "\n".join(productos_sin_stock)
                messages.error(request, mensaje_error)
                return redirect('detalle_pedido', pedido_id=pedido.id)

            # 🔻 Descontar stock de cada producto
            for detalle in detalles:
                producto = detalle.producto
                producto.stock -= detalle.cantidad
                producto.save()

            # 💰 Calcular totales
            subtotal = sum(detalle.cantidad * detalle.producto.precio_unitario for detalle in detalles)
            iva = subtotal * Decimal('0.19')
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

    except Exception as e:
        messages.error(request, 'Ocurrió un error inesperado al confirmar el pedido.')
        print(e)

    return redirect('detalle_pedido', pedido_id=pedido.id)


# =========================
# MARCAR PEDIDO COMO ENVIADO
# =========================
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


@login_required
def estadisticas_ventas(request):
    # Solo administradores pueden acceder
    if request.user.rol != 'Administrador':
        messages.error(request, "⚠️ No tienes permisos para acceder a esta sección.")
        return redirect('dashboard')

    # Obtener pedidos enviados
    pedidos = Pedido.objects.filter(estado='Enviado').select_related('cliente', 'usuario').order_by('-fecha_creacion')

    # Filtros por fecha
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')

    if fecha_desde:
        pedidos = pedidos.filter(fecha_creacion__date__gte=fecha_desde)
    if fecha_hasta:
        pedidos = pedidos.filter(fecha_creacion__date__lte=fecha_hasta)

    # Calcular totales
    total_ventas = pedidos.count()
    monto_total = 0
    
    # Calcular monto total desde los documentos asociados
    for pedido in pedidos:
        documento = DocumentoVenta.objects.filter(pedido=pedido).first()
        if documento:
            monto_total += documento.total

    context = {
        'pedidos': pedidos,
        'total_ventas': total_ventas,
        'monto_total': monto_total,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
    }

    return render(request, 'ventas/estadisticas_ventas.html', context)


@login_required
def exportar_ventas_excel(request):
    # Solo administradores pueden exportar
    if request.user.rol != 'Administrador':
        messages.error(request, "⚠️ No tienes permisos para exportar.")
        return redirect('dashboard')

    # Obtener pedidos enviados
    pedidos = Pedido.objects.filter(estado='Enviado').select_related('cliente', 'usuario').order_by('-fecha_creacion')

    # Aplicar filtros de fecha si existen
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')

    if fecha_desde:
        pedidos = pedidos.filter(fecha_creacion__date__gte=fecha_desde)
    if fecha_hasta:
        pedidos = pedidos.filter(fecha_creacion__date__lte=fecha_hasta)

    # Crear el archivo Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "Ventas"

    # Estilos
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=12)
    header_alignment = Alignment(horizontal="center", vertical="center")

    # Encabezados
    headers = ['Pedido #', 'Cliente', 'RUT', 'Vendedor', 'Fecha', 'Estado', 'Total']
    ws.append(headers)

    # Aplicar estilo a encabezados
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment

    # Agregar datos
    for pedido in pedidos:
        documento = DocumentoVenta.objects.filter(pedido=pedido).first()
        total = documento.total if documento else 0

        ws.append([
            pedido.id,
            pedido.cliente.razon_social,
            pedido.cliente.rut,
            pedido.usuario.get_full_name() or pedido.usuario.username,
            pedido.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
            pedido.estado,
            f"${total:,.0f}"
        ])

    # Ajustar ancho de columnas
    ws.column_dimensions['A'].width = 12
    ws.column_dimensions['B'].width = 30
    ws.column_dimensions['C'].width = 15
    ws.column_dimensions['D'].width = 25
    ws.column_dimensions['E'].width = 20
    ws.column_dimensions['F'].width = 15
    ws.column_dimensions['G'].width = 15

    # Preparar respuesta HTTP
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    
    # Nombre del archivo con fecha actual
    filename = f"ventas_{date.today().strftime('%d-%m-%Y')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # Guardar el archivo en la respuesta
    wb.save(response)
    return response