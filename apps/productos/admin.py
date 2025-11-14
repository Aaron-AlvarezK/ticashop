from django.contrib import admin
from django.utils.html import format_html
from .models import Categoria, Producto

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'activa']
    list_filter = ['activa']
    search_fields = ['nombre']
    list_editable = ['activa']

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'foto_tag', 'precio_unitario', 'stock', 'activo')
    readonly_fields = ('foto_preview',)
    fields = (
        'codigo', 'nombre', 'descripcion',
        'foto', 'foto_preview',
        'categoria', 'proveedor',
        'precio_unitario', 'costo_unitario',
        'stock', 'stock_minimo',
        'afecto_iva', 'activo',
    )

    def foto_tag(self, obj):
        if obj.foto:
            return format_html('<img src="{}" style="width:40px;height:40px;object-fit:cover;border-radius:4px;" />', obj.foto.url)
        return '-'
    foto_tag.short_description = 'Foto'

    def foto_preview(self, obj):
        if obj.foto:
            return format_html('<img src="{}" style="max-width:300px;max-height:300px;object-fit:contain;" />', obj.foto.url)
        return 'Sin imagen'
    foto_preview.short_description = 'Vista previa'