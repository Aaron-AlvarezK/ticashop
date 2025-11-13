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


from django.db.models import Sum

def listar_documentos(request):
    facturas = (
        DocumentoVenta.objects
        .filter(tipo_documento='Factura')
        .select_related('cliente', 'vendedor', 'pedido')
        .order_by('-fecha_emision', '-folio')  # clave: ordenar por fecha_emision
    )
    return render(request, 'documentos/listar_documentos.html', {'facturas': facturas})

# ========== CREAR DOCUMENTO DESDE PEDIDO ==========
@login_required
def crear_documento_desde_pedido(request, pedido_id):
    """Crea un documento de venta a partir de un pedido"""
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    # Verificar si ya tiene documento
    if hasattr(pedido, 'documento'):
        messages.warning(request, 'Este pedido ya tiene un documento asociado.')
        return redirect('detalle_documento', documento_id=pedido.documento.id)
    
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
                return redirect('detalle_documento', documento_id=documento.id)
    else:
        form = DocumentoVentaForm(initial={'cliente': pedido.cliente})
    
    context = {
        'form': form,
        'pedido': pedido,
    }
    return render(request, 'documentos/crear_documento.html', context)


# ========== DETALLE DE DOCUMENTO ==========
@login_required
def detalle_documento(request, documento_id):
    """Muestra el detalle completo de un documento"""
    documento = get_object_or_404(
        DocumentoVenta.objects.select_related('cliente', 'vendedor', 'pedido')
        .prefetch_related('detalles__producto', 'pagos'),
        id=documento_id
    )
    
    context = {
        'documento': documento,
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
                return redirect('registrar_pago', documento_id=documento.id)
            
            pago.save()
            messages.success(request, 'Pago registrado exitosamente.')
            return redirect('detalle_documento', documento_id=documento.id)
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
        return redirect('listar_documentos')
    
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
        return redirect('detalle_documento', documento_id=pedido.documento.id)

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
            
            return redirect('detalle_documento', documento_id=doc.id)
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