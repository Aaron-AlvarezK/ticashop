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


# ========== LISTAR DOCUMENTOS ==========
@login_required
def listar_documentos(request):
    """Lista todos los documentos de venta"""
    documentos = DocumentoVenta.objects.select_related(
        'cliente', 'vendedor'
    ).prefetch_related('detalles').all()
    
    # Filtros opcionales
    tipo = request.GET.get('tipo')
    estado = request.GET.get('estado')
    
    if tipo:
        documentos = documentos.filter(tipo_documento=tipo)
    if estado:
        documentos = documentos.filter(estado=estado)
    
    context = {
        'documentos': documentos,
        'tipos': DocumentoVenta.TIPOS_DOCUMENTO,
        'estados': DocumentoVenta.ESTADOS_DOCUMENTO,
    }
    return render(request, 'documentos/listar_documentos.html', context)


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