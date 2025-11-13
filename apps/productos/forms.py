from django import forms
from .models import Producto

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            'codigo', 'nombre', 'descripcion',
            'categoria', 'proveedor', 'precio_unitario', 'costo_unitario',
            'stock', 'stock_minimo', 'afecto_iva', 'activo'
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }