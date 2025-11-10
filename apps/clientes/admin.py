from django.contrib import admin
from .models import Cliente, Proveedor

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['rut', 'razon_social', 'giro', 'email_facturacion', 'cantidad_pedidos']
    search_fields = ['rut', 'razon_social', 'giro']
    list_filter = ['giro']
    
    def cantidad_pedidos(self, obj):
        return obj.pedido_set.count()
    cantidad_pedidos.short_description = 'Pedidos'

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ['rut', 'razon_social', 'email_contacto', 'telefono', 'cantidad_productos']
    search_fields = ['rut', 'razon_social']
    
    def cantidad_productos(self, obj):
        return obj.producto_set.count()
    cantidad_productos.short_description = 'Productos'