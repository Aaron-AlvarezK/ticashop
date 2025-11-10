from django.contrib import admin
from .models import DocumentoVenta, DetalleDocumento, Pago

class DetalleDocumentoInline(admin.TabularInline):
    model = DetalleDocumento
    extra = 1
    readonly_fields = ['subtotal']

class PagoInline(admin.TabularInline):
    model = Pago
    extra = 1
    readonly_fields = ['fecha_pago']

@admin.register(DocumentoVenta)
class DocumentoVentaAdmin(admin.ModelAdmin):
    list_display = [
        'folio',
        'tipo_documento', 
        'cliente', 
        'fecha_emision',
        'total', 
        'estado',
    ]
    list_filter = ['tipo_documento', 'estado', 'fecha_emision']
    search_fields = ['folio', 'cliente__razon_social', 'cliente__rut']
    readonly_fields = ['fecha_emision']
    inlines = [DetalleDocumentoInline, PagoInline]
    
    # FIELDSET SIMPLIFICADO - sin propiedades problemáticas
    fieldsets = (
        ('Información del Documento', {
            'fields': ('tipo_documento', 'folio', 'cliente', 'vendedor', 'pedido')
        }),
        ('Montos', {
            'fields': ('neto', 'iva', 'total')
        }),
        ('Fechas y Estado', {
            'fields': ('fecha_emision', 'fecha_vencimiento', 'estado', 'medio_de_pago')
        }),
    )

@admin.register(DetalleDocumento)
class DetalleDocumentoAdmin(admin.ModelAdmin):
    list_display = ['documento', 'producto', 'cantidad', 'precio_unitario_venta', 'subtotal']
    list_filter = ['documento__tipo_documento']
    search_fields = ['producto__nombre', 'documento__folio']

@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ['id', 'documento', 'fecha_pago', 'monto_pagado', 'metodo_pago']
    list_filter = ['metodo_pago', 'fecha_pago']
    search_fields = ['documento__folio', 'referencia']
    readonly_fields = ['fecha_pago']