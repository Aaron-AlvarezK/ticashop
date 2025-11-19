from django import forms
from .models import Producto

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            'codigo', 'nombre', 'descripcion', 'foto',
            'categoria', 'proveedor', 'precio_unitario', 'costo_unitario',
            'stock', 'stock_minimo', 'afecto_iva', 'activo'
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }


# --- AÑADE ESTE NUEVO FORMULARIO ---
class ImportCostoForm(forms.Form):
    """
    Formulario para subir el archivo Excel con los costos.
    """
    archivo_excel = forms.FileField(
        label="Seleccionar archivo Excel (.xlsx)",
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.xlsx'})
    )