from django import forms
from .models import DocumentoVenta, DetalleDocumento, Pago
from apps.clientes.models import Cliente
from apps.productos.models import Producto

class DocumentoVentaForm(forms.ModelForm):
    class Meta:
        model = DocumentoVenta
        fields = [
            'tipo_documento', 'cliente', 'fecha_vencimiento', 
            'medio_de_pago'
        ]
        widgets = {
            'tipo_documento': forms.Select(attrs={'class': 'form-control'}),
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'fecha_vencimiento': forms.DateInput(attrs={
                'class': 'form-control', 
                'type': 'date'
            }),
            'medio_de_pago': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'tipo_documento': 'Tipo de Documento',
            'cliente': 'Cliente',
            'fecha_vencimiento': 'Fecha de Vencimiento (opcional)',
            'medio_de_pago': 'Medio de Pago',
        }

class DetalleDocumentoForm(forms.ModelForm):
    class Meta:
        model = DetalleDocumento
        fields = ['producto', 'cantidad', 'precio_unitario_venta']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '1'
            }),
            'precio_unitario_venta': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01'
            }),
        }

class PagoForm(forms.ModelForm):
    class Meta:
        model = Pago
        fields = ['monto_pagado', 'metodo_pago', 'referencia', 'observaciones']
        widgets = {
            'monto_pagado': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01',
                'placeholder': 'Monto a pagar'
            }),
            'metodo_pago': forms.Select(attrs={'class': 'form-control'}),
            'referencia': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de operación o referencia'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones adicionales'
            }),
        }
        labels = {
            'monto_pagado': 'Monto a Pagar',
            'metodo_pago': 'Método de Pago',
            'referencia': 'Referencia',
            'observaciones': 'Observaciones',
        }
    
    def __init__(self, *args, **kwargs):
        documento = kwargs.pop('documento', None)
        super().__init__(*args, **kwargs)
        
        # Prellenar el método de pago si el documento ya tiene uno
        if documento and documento.medio_de_pago:
            self.fields['metodo_pago'].initial = documento.medio_de_pago