from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Q
from decimal import Decimal

from .models import DocumentoVenta, DetalleDocumento, Pago
from .forms import DocumentoVentaForm, DetalleDocumentoForm, PagoForm
from apps.ventas.models import Pedido
from apps.productos.models import Producto

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from apps.documentos.models import DocumentoVenta, DetalleDocumento

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal

from .models import DocumentoVenta, DetalleDocumento, NotaCredito, DetalleNotaCredito
from .forms import NotaCreditoForm, DetalleNotaFormSet

from .models import DocumentoVenta, DetalleDocumento, NotaCredito, DetalleNotaCredito
from .forms import NotaCreditoForm, DetalleNotaFormSet


from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

from .models import NotaCredito, DetalleNotaCredito

from django.db.models import Sum

# apps/documentos/views.py
from django.utils import timezone
from datetime import timedelta

# apps/documentos/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count

from .models import DocumentoVenta
from apps.clientes.models import Cliente

@login_required
def listar_documentos(request):
    # Inicializar la consulta base para solo Facturas
    consulta_base = DocumentoVenta.objects.filter(tipo_documento='Factura')
    
    # --- FILTRO DE SEGURIDAD PARA CLIENTES ---
    if request.user.rol == 'Cliente':
        try:
            # Filtramos por el perfil de cliente asociado al usuario logueado
            perfil_cliente = request.user.perfil_cliente
            consulta_base = consulta_base.filter(cliente=perfil_cliente)
        except Cliente.DoesNotExist:
            # Si el usuario es cliente pero no ha completado el perfil, no ve nada.
            consulta_base = consulta_base.none()
            messages.warning(request, "⚠️ Debes completar tu perfil para ver tus documentos.")
            
    # Continuar con el resto de la consulta
    facturas = (
        consulta_base
        .select_related('cliente', 'vendedor')
        .annotate(nc_count=Count('notas_credito'))
        .order_by('-fecha_emision')
    )

    hoy = timezone.localdate()
    for f in facturas:
        f.puede_crear_nota = False
        if f.fecha_emision:
            fecha_emision_date = f.fecha_emision.date() if hasattr(f.fecha_emision, 'date') else f.fecha_emision
            limite = fecha_emision_date + timedelta(days=30)
            f.puede_crear_nota = (hoy <= limite) and (f.estado != 'Anulada')

    return render(request, 'documentos/listar_documentos.html', {
        'facturas': facturas,
    })
# ========== CREAR DOCUMENTO DESDE PEDIDO ==========
@login_required
def crear_documento_desde_pedido(request, pedido_id):
    """Crea un documento de venta a partir de un pedido"""
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    # Verificar si ya tiene documento
    if hasattr(pedido, 'documento'):
        messages.warning(request, 'Este pedido ya tiene un documento asociado.')
        return redirect('documentos:detalle_documento', documento_id=pedido.documento.id)
    
    if request.method == 'POST':
        form = DocumentoVentaForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                # Crear documento
                documento = form.save(commit=False)
                documento.vendedor = request.user
                documento.pedido = pedido
                documento.cliente = pedido.cliente
                
                # Generar folio automático
                ultimo_folio = DocumentoVenta.objects.filter(
                    tipo_documento=documento.tipo_documento
                ).order_by('-folio').first()
                
                documento.folio = (ultimo_folio.folio + 1) if ultimo_folio else 1
                
                # Calcular totales
                neto = Decimal('0')
                for detalle in pedido.detalles.all():
                    neto += detalle.subtotal
                
                documento.neto = neto
                documento.iva = neto * Decimal('0.19')  # IVA 19%
                documento.total = neto + documento.iva
                documento.save()
                
                # Crear detalles del documento
                for detalle_pedido in pedido.detalles.all():
                    DetalleDocumento.objects.create(
                        documento=documento,
                        producto=detalle_pedido.producto,
                        cantidad=detalle_pedido.cantidad,
                        precio_unitario_venta=detalle_pedido.precio_unitario,
                        costo_unitario_venta=detalle_pedido.producto.costo_unitario
                    )
                
                messages.success(request, f'{documento.tipo_documento} #{documento.folio} creada exitosamente.')
                return redirect('documentos:detalle_documento', documento_id=documento.id)
    else:
        form = DocumentoVentaForm(initial={'cliente': pedido.cliente})
    
    context = {
        'form': form,
        'pedido': pedido,
    }
    return render(request, 'documentos/crear_documento.html', context)




# apps/documentos/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .models import DocumentoVenta, DetalleDocumento

@login_required
def detalle_documento(request, documento_id):
    """
    Muestra el detalle de un documento. Si es Factura se renderiza el layout de factura,
    si es Boleta se renderiza el layout de boleta (ver template).
    """
    doc = get_object_or_404(DocumentoVenta.objects.select_related('cliente', 'vendedor'), id=documento_id)

    items = DetalleDocumento.objects.filter(documento=doc).select_related('producto')

    empresa = {
        'nombre': 'TICASHOP SPA',
        'rut': '99.999.999-9',
        'giro': 'Venta de productos tecnológicos',
        'direccion': 'Av. Ejemplo 1234',
        'ciudad': 'Santiago',
        'telefono': '+56 9 1234 5678',
        'email': 'contacto@ticashop.cl',
        'sucursal': 'SANTIAGO',
    }

    neto = doc.neto or Decimal('0')
    iva = doc.iva or Decimal('0')
    total = doc.total or (neto + iva)

    is_factura = (doc.tipo_documento == 'Factura')

    show_nc_button = False
    if is_factura and doc.fecha_emision:
        fecha_emision_date = doc.fecha_emision.date() if hasattr(doc.fecha_emision, 'date') else doc.fecha_emision
        limite = fecha_emision_date + timedelta(days=30)
        show_nc_button = (timezone.localdate() <= limite) and (doc.estado not in ['Anulada', 'Devuelta'])

    context = {
        'doc': doc,
        'items': items,
        'empresa': empresa,
        'neto': neto,
        'iva': iva,
        'total': total,
        'is_factura': is_factura,
        'show_nc_button': show_nc_button,
    }

    return render(request, 'documentos/detalle_documento.html', context)
# views.py (añádelo o reemplaza la función existente)
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .models import DocumentoVenta, DetalleDocumento

@login_required
def detalle_documento(request, documento_id):
    """
    Muestra detalle de documento con layout distinto para Factura / Boleta.
    El contexto esperado por la plantilla:
    doc, items, empresa, neto, iva, total, is_factura, show_nc_button
    """
    doc = get_object_or_404(DocumentoVenta.objects.select_related('cliente','vendedor'), id=documento_id)

    # Items (sigues usando DetalleDocumento)
    items = DetalleDocumento.objects.filter(documento=doc).select_related('producto')

    # Datos de la empresa (sustituye por tu modelo Empresa si lo prefieres)
    empresa = {
        'nombre': 'TICASHOP SPA',
        'rut': '99.999.999-9',
        'giro': 'Venta de productos tecnológicos',
        'direccion': 'Av. Ejemplo 1234',
        'ciudad': 'Santiago',
        'telefono': '+56 9 1234 5678',
        'email': 'contacto@ticashop.cl',
        'sucursal': 'SANTIAGO',
    }

    # Totales (aseguramos no None)
    neto = doc.neto or Decimal('0')
    iva = doc.iva or Decimal('0')
    total = doc.total or (neto + iva)

    # Flag para template
    is_factura = (doc.tipo_documento == 'Factura')

    # Mostrar botón NC solo para facturas dentro del plazo de 30 días y no anuladas/devueltas
    show_nc_button = False
    if is_factura and doc.fecha_emision:
        fecha_emision_date = doc.fecha_emision.date() if hasattr(doc.fecha_emision, 'date') else doc.fecha_emision
        limite = fecha_emision_date + timedelta(days=30)
        show_nc_button = (timezone.localdate() <= limite) and (doc.estado not in ['Anulada', 'Devuelta', 'Devuelta Parcial'])

    context = {
        'doc': doc,
        'items': items,
        'empresa': empresa,
        'neto': neto,
        'iva': iva,
        'total': total,
        'is_factura': is_factura,
        'show_nc_button': show_nc_button,
    }
    return render(request, 'documentos/detalle_documento.html', context)
# ========== REGISTRAR PAGO ==========
@login_required
def registrar_pago(request, documento_id):
    """Registra un pago para un documento"""
    documento = get_object_or_404(DocumentoVenta, id=documento_id)
    
    if request.method == 'POST':
        form = PagoForm(request.POST, documento=documento)
        if form.is_valid():
            pago = form.save(commit=False)
            pago.documento = documento
            
            # Validar que no se pague más del saldo pendiente
            if pago.monto_pagado > documento.saldo_pendiente:
                messages.error(request, f'El monto excede el saldo pendiente (${documento.saldo_pendiente})')
                return redirect('documentos:registrar_pago', documento_id=documento.id)
            
            pago.save()
            messages.success(request, 'Pago registrado exitosamente.')
            return redirect('documentos:detalle_documento', documento_id=documento.id)
    else:
        form = PagoForm(documento=documento, initial={
            'monto_pagado': documento.saldo_pendiente
        })
    
    context = {
        'form': form,
        'documento': documento,
    }
    return render(request, 'documentos/registrar_pago.html', context)


# ========== ANULAR DOCUMENTO ==========
@login_required
def anular_documento(request, documento_id):
    """Anula un documento de venta"""
    documento = get_object_or_404(DocumentoVenta, id=documento_id)
    
    if request.method == 'POST':
        if documento.estado == 'Pagada':
            messages.error(request, 'No se puede anular un documento que ya está pagado.')
        else:
            documento.estado = 'Anulada'
            documento.save()
            messages.success(request, f'{documento.tipo_documento} #{documento.folio} anulada.')
        return redirect('documentos:listar_documentos')
    
    return render(request, 'documentos/confirmar_anular.html', {'documento': documento})


# apps/documentos/views.py
from datetime import timedelta
from django.utils import timezone
from decimal import Decimal

@login_required
@transaction.atomic
def crear_documento_desde_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido.objects.select_related('cliente').prefetch_related('detalles__producto'),
                                id=pedido_id)

    if hasattr(pedido, 'documento'):
        messages.warning(request, 'Este pedido ya tiene un documento asociado.')
        return redirect('documentos:detalle_documento', documento_id=pedido.documento.id)

    if request.method == 'POST':
        form = DocumentoVentaForm(request.POST)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.vendedor = request.user
            doc.pedido = pedido
            doc.cliente = pedido.cliente
            
            # Procesar modalidad de pago
            modalidad = form.cleaned_data.get('modalidad_pago')
            dias_plazo = form.cleaned_data.get('dias_plazo')
            
            hoy = timezone.localdate()
            doc.fecha_emision = timezone.now()
            
            if modalidad == 'ahora':
                # Pago inmediato: sin vencimiento o vence hoy
                doc.fecha_vencimiento = None  # o hoy si prefieres
                doc.estado = 'Pagada'  # Marcar como pagada directamente
                messages.success(request, 'Factura creada y marcada como PAGADA (pago inmediato)')
            else:
                # Pago a plazos: calcular vencimiento
                dias = int(dias_plazo) if dias_plazo else 30
                doc.fecha_vencimiento = hoy + timedelta(days=dias)
                doc.estado = 'Emitida'
                messages.success(request, f'Factura creada. Vence el {doc.fecha_vencimiento.strftime("%d/%m/%Y")}')
            
            # Calcular totales desde el pedido
            neto = Decimal('0')
            for dp in pedido.detalles.all():
                neto += dp.subtotal
            
            doc.neto = neto
            doc.iva = (neto * Decimal('0.19')).quantize(Decimal('1.'))
            doc.total = doc.neto + doc.iva
            
            doc.save()  # Aquí se asigna el folio automáticamente
            
            # Copiar detalles del pedido al documento
            for dp in pedido.detalles.all():
                DetalleDocumento.objects.create(
                    documento=doc,
                    producto=dp.producto,
                    cantidad=dp.cantidad,
                    precio_unitario_venta=dp.precio_unitario,
                    costo_unitario_venta=dp.producto.costo_unitario,
                )
            
            return redirect('documentos:detalle_documento', documento_id=doc.id)
    else:
        form = DocumentoVentaForm(initial={'cliente': pedido.cliente})

    return render(request, 'documentos/crear_documento.html', {
        'form': form,
        'pedido': pedido,
    })


def esta_vencida(self):
    """Verifica si la factura está vencida"""
    try:
        if self.fecha_vencimiento and self.estado in ['Emitida', 'Pago Parcial']:
            return timezone.now().date() > self.fecha_vencimiento
        return False
    except:
        return False
    


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from decimal import Decimal

from .models import DocumentoVenta, DetalleDocumento, NotaCredito, DetalleNotaCredito
from .forms import NotaCreditoForm, DetalleNotaFormSet

@login_required
def crear_nota_credito(request, factura_id):
    factura = get_object_or_404(DocumentoVenta, id=factura_id)

    # Validación plazo 30 días (usar date() si fecha_emision es datetime)
    if factura.fecha_emision:
        fecha_emision_date = factura.fecha_emision.date() if hasattr(factura.fecha_emision, 'date') else factura.fecha_emision
        limite = fecha_emision_date + timedelta(days=30)
        if timezone.localdate() > limite:
            messages.error(request, 'No se puede emitir una nota de crédito: la factura supera el plazo de 30 días.')
            return redirect('documentos:detalle_documento', documento_id=factura.id)

    items_factura = DetalleDocumento.objects.filter(documento=factura).select_related('producto')

    if request.method == 'POST':
        nota_form = NotaCreditoForm(request.POST)
        detalles_formset = DetalleNotaFormSet(request.POST)

        if nota_form.is_valid() and detalles_formset.is_valid():
            monto_total = Decimal('0')
            items_para_guardar = []

            # Validar cantidades y calcular montos
            for form in detalles_formset:
                prod_id = form.cleaned_data.get('producto_id')
                cantidad_dev = int(form.cleaned_data.get('cantidad') or 0)
                precio = form.cleaned_data.get('precio_unitario') or Decimal('0')

                original = next((it for it in items_factura if (it.producto and it.producto.id) == prod_id), None)
                cantidad_orig = original.cantidad if original else 0

                if cantidad_dev < 0 or cantidad_dev > cantidad_orig:
                    messages.error(request, f'Cantidad inválida para producto {original.producto.nombre if original else prod_id}. Máximo permitido: {cantidad_orig}')
                    return render(request, 'documentos/crear_nota_credito.html', {
                        'factura': factura,
                        'nota_form': nota_form,
                        'detalles_formset': detalles_formset,
                        'items': items_factura
                    })

                if cantidad_dev > 0:
                    subtotal = (Decimal(precio) or Decimal('0')) * cantidad_dev
                    monto_total += subtotal
                    items_para_guardar.append({
                        'producto': original.producto if original else None,
                        'descripcion': original.producto.nombre if original else '',
                        'cantidad': cantidad_dev,
                        'precio_unitario': Decimal(precio),
                        'subtotal': subtotal
                    })

            if monto_total <= 0:
                messages.error(request, 'Debes indicar al menos un producto con cantidad mayor a 0 para generar la nota.')
                return render(request, 'documentos/crear_nota_credito.html', {
                    'factura': factura,
                    'nota_form': nota_form,
                    'detalles_formset': detalles_formset,
                    'items': items_factura
                })

            # Guardar todo en una transacción
            try:
                with transaction.atomic():
                    nota = nota_form.save(commit=False)
                    nota.factura = factura
                    nota.usuario = request.user
                    nota.monto = monto_total
                    nota.save()

                    for it in items_para_guardar:
                        detalle_nc = DetalleNotaCredito.objects.create(
                            nota=nota,
                            producto=it['producto'],
                            descripcion=it['descripcion'],
                            cantidad=it['cantidad'],
                            precio_unitario=it['precio_unitario'],
                            subtotal=it['subtotal']
                        )

                        # Reingresar stock: solo si el producto existe y tiene campo stock
                        prod = it['producto']
                        if prod:
                            try:
                                # Asegúrate de que tu modelo Producto tiene el campo 'stock'
                                prod.stock = (prod.stock or 0) + int(it['cantidad'])
                                prod.save()
                            except Exception as e:
                                # No fallamos la transacción por un problema de stock, pero lo registramos
                                print(f"Warning: no se pudo actualizar stock para producto {prod.id}: {e}")

                    # Actualizar estado de la factura según monto devuelto vs total
                    if monto_total >= (factura.total or Decimal('0')):
                        factura.estado = 'Devuelta'
                    else:
                        factura.estado = 'Devuelta Parcial'
                    factura.save()

            except Exception as e:
                messages.error(request, f'Error al crear la nota de crédito: {e}')
                # Para depuración, imprime errores en consola
                print("Error creando NC:", e)
                return render(request, 'documentos/crear_nota_credito.html', {
                    'factura': factura,
                    'nota_form': nota_form,
                    'detalles_formset': detalles_formset,
                    'items': items_factura
                })

            # Todo OK -> PRG: redirigir al detalle de la nota y mostrar mensaje
            messages.success(request, f'Nota de crédito creada correctamente (Monto: ${monto_total:,}).')
            return redirect('documentos:detalle_nota_credito', nota_id=nota.id)

        else:
            # DEBUG: mostrar errores en consola y pasar info al template
            print("=== DEBUG NotaCredito ===")
            print("NotaForm errors:", nota_form.errors)
            print("Formset non_form_errors:", detalles_formset.non_form_errors())
            print("Formset total forms:", detalles_formset.total_form_count())
            for i, f in enumerate(detalles_formset):
                print(f"Form {i} errors:", f.errors)
            print("REQUEST.POST keys:", list(request.POST.keys()))
            # pasar debug al template para que lo veas sin abrir consola
            debug_info = {
                'nota_errors': nota_form.errors,
                'formset_non_field': detalles_formset.non_form_errors(),
                'formset_errors': [f.errors for f in detalles_formset],
                'post_keys': list(request.POST.keys()),
                'total_forms': detalles_formset.total_form_count(),
            }
            messages.error(request, "Hay errores en el formulario. Revisa los campos.")
            return render(request, 'documentos/crear_nota_credito.html', {
                'factura': factura,
                'nota_form': nota_form,
                'detalles_formset': detalles_formset,
                'items': items_factura,
                'debug_info': debug_info,   # <- nuevo
            })
    else:
        # GET: inicializar form con items
        nota_form = NotaCreditoForm(initial={'fecha_emision': timezone.localdate()})
        initial_items = []
        for it in items_factura:
            initial_items.append({
                'producto_id': it.producto.id if it.producto else None,
                'producto_nombre': it.producto.nombre if it.producto else 'Sin nombre',
                'cantidad_original': it.cantidad,
                'cantidad': 0,
                'precio_unitario': it.precio_unitario_venta,
            })
        detalles_formset = DetalleNotaFormSet(initial=initial_items)

    return render(request, 'documentos/crear_nota_credito.html', {
        'factura': factura,
        'nota_form': nota_form,
        'detalles_formset': detalles_formset,
        'items': items_factura
    })



from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

from .models import NotaCredito

@login_required
def detalle_nota_credito(request, nota_id):
    # Cargar la nota + factura relacionada y detalles con producto
    nota = get_object_or_404(NotaCredito.objects.select_related('factura', 'usuario'), id=nota_id)
    detalles = nota.detalles.select_related('producto').all()

    empresa = {
        'nombre': 'TICASHOP SPA',
        'rut': '99.999.999-9',
        'giro': 'Venta de productos tecnológicos',
        'direccion': 'Av. Ejemplo 1234',
        'ciudad': 'Santiago',
        'telefono': '+56 9 1234 5678',
        'email': 'contacto@ticashop.cl',
        'sucursal': 'SANTIAGO',
    }

    context = {
        'nota': nota,
        'detalles': detalles,
        'empresa': empresa,
    }
    return render(request, 'documentos/detalle_nota_credito.html', context)