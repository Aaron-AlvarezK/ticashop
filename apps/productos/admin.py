from django.contrib import admin
from .models import Categoria, Producto

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'activa']
    list_filter = ['activa']
    search_fields = ['nombre']
    list_editable = ['activa']

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = [
        'codigo', 
        'nombre', 
        'categoria', 
        'precio_unitario', 
        'stock', 
        'mostrar_stock_bajo',
        'activo'
    ]
    list_filter = ['categoria', 'activo', 'afecto_iva']
    search_fields = ['codigo', 'nombre', 'descripcion']
    list_editable = ['precio_unitario', 'stock', 'activo']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    # FIELDSET SIMPLIFICADO - sin campos calculados
    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo', 'nombre', 'descripcion', 'categoria')
        }),
        ('Precios y Costos', {
            'fields': ('precio_unitario', 'costo_unitario')
        }),
        ('Inventario', {
            'fields': ('stock', 'stock_minimo')
        }),
        ('Proveedor e Impuestos', {
            'fields': ('proveedor', 'afecto_iva')
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
    )
    
    def mostrar_stock_bajo(self, obj):
        return obj.tiene_stock_bajo
    mostrar_stock_bajo.boolean = True
    mostrar_stock_bajo.short_description = 'Stock Bajo'