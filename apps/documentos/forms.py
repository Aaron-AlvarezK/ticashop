from django import forms
from .models import DocumentoVenta, DetalleDocumento, Pago
from apps.clientes.models import Cliente
from apps.productos.models import Producto

class DocumentoVentaForm(forms.ModelForm):
    # Campos adicionales para modalidad de pago
    MODALIDADES = (
        ('ahora', 'Pagar ahora'),
        ('plazos', 'Pagar a plazos'),
    )
    
    DIAS_PLAZO_CHOICES = (
        (15, '15 días'),
        (30, '30 días'),
        (45, '45 días'),
        (60, '60 días'),
        (90, '90 días'),
    )
    
    modalidad_pago = forms.ChoiceField(
        choices=MODALIDADES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Modalidad de pago',
        initial='ahora'
    )
    
    dias_plazo = forms.ChoiceField(
        choices=DIAS_PLAZO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Días de plazo',
        initial=30
    )
    
    class Meta:
        model = DocumentoVenta
        fields = [
            'tipo_documento', 'cliente', 'medio_de_pago'
        ]
        widgets = {
            'tipo_documento': forms.Select(attrs={'class': 'form-control'}),
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'medio_de_pago': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'tipo_documento': 'Tipo de Documento',
            'cliente': 'Cliente',
            'medio_de_pago': 'Medio de Pago',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer que dias_plazo no sea requerido por defecto
        self.fields['dias_plazo'].required = False


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