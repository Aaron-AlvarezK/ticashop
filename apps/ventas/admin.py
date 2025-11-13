from django.contrib import admin
from .models import Pedido, DetallePedido

class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 1
    readonly_fields = ['subtotal']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('producto')

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = [
        'id', 
        'cliente', 
        'usuario', 
        'fecha_creacion', 
        'total', 
        'estado',
        'cantidad_items'
    ]
    list_filter = ['estado', 'fecha_creacion', 'usuario']
    search_fields = ['cliente__razon_social', 'cliente__rut']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion', 'total']
    list_editable = ['estado']
    inlines = [DetallePedidoInline]
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('cliente', 'usuario', 'estado', 'total')
        }),
        ('Información de Despacho', {
            'fields': ('direccion_despacho', 'observaciones')
        }),
        ('Auditoría', {
            'fields': ('fecha_creacion', 'fecha_actualizacion')
        }),
    )
    
    def cantidad_items(self, obj):
        return obj.cantidad_items
    cantidad_items.short_description = 'Items'

@admin.register(DetallePedido)
class DetallePedidoAdmin(admin.ModelAdmin):
    list_display = ['pedido', 'producto', 'cantidad', 'precio_unitario_venta', 'subtotal']
    list_filter = ['pedido__estado']
    search_fields = ['producto__nombre', 'pedido__cliente__razon_social']