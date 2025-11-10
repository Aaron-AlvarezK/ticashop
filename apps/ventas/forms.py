from django import forms
from .models import Pedido, DetallePedido
from apps.productos.models import Producto
from apps.clientes.models import Cliente

class PedidoForm(forms.ModelForm):
    class Meta:
        model = Pedido
        fields = ['cliente', 'direccion_despacho', 'observaciones', 'estado']
        widgets = {
            'direccion_despacho': forms.Textarea(attrs={'rows': 3}),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }

class DetallePedidoForm(forms.ModelForm):
    class Meta:
        model = DetallePedido
        fields = ['producto', 'cantidad', 'precio_unitario_venta']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo mostrar productos activos con stock
        self.fields['producto'].queryset = Producto.objects.filter(activo=True, stock__gt=0)
    
    def clean(self):
        cleaned_data = super().clean()
        producto = cleaned_data.get('producto')
        cantidad = cleaned_data.get('cantidad')
        
        if producto and cantidad:
            # Validar stock disponible
            if cantidad > producto.stock:
                raise forms.ValidationError(
                    f'Stock insuficiente. Disponible: {producto.stock} unidades'
                )
            
            # Si no se especificó precio, usar el del producto
            if not cleaned_data.get('precio_unitario_venta'):
                cleaned_data['precio_unitario_venta'] = producto.precio_unitario
        
        return cleaned_data