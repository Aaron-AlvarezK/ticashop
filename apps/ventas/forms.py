from django import forms
from .models import Pedido, DetallePedido
from apps.clientes.models import Cliente
from apps.productos.models import Producto
from apps.documentos.models import DocumentoVenta
from datetime import date
from apps.documentos.models import DocumentoVenta, DetalleDocumento  


class PedidoForm(forms.ModelForm):
    class Meta:
        model = Pedido
        fields = ['cliente', 'observaciones']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones del pedido (opcional)'
            }),
        }

class TipoDocumentoForm(forms.Form):
    """Formulario para elegir el tipo de documento"""
    TIPO_CHOICES = [
        ('', '-- Seleccione tipo de documento --'),
        ('Boleta', 'Boleta'),
        ('Factura', 'Factura'),
    ]
    
    tipo_documento = forms.ChoiceField(
        choices=TIPO_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control form-control-lg',
            'id': 'id_tipo_documento'
        }),
        label='Tipo de Documento'
    )

class BoletaForm(forms.Form):
    """Formulario específico para Boleta"""
    medio_de_pago = forms.ChoiceField(
        choices=DocumentoVenta.MEDIOS_PAGO,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Medio de Pago'
    )
    
    observaciones = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Observaciones adicionales (opcional)'
        }),
        label='Observaciones'
    )

class FacturaForm(forms.Form):
    razon_social = forms.CharField(
        label="Razón Social",
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Comercial ABC Ltda.'})
    )

    rut = forms.CharField(
        label="RUT",
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 76.123.456-7'}),
        help_text="Debe tener formato xx.xxx.xxx-x"
    )

    giro = forms.CharField(
        label="Giro Comercial",
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Venta de repuestos'})
    )

    direccion = forms.CharField(
        label="Dirección",
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Calle, número, oficina...'})
    )

    ciudad = forms.CharField(
        label="Ciudad",
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    comuna = forms.CharField(
        label="Comuna",
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    medio_de_pago = forms.ChoiceField(
        label="Medio de Pago",
        choices=[
            ('Transferencia', 'Transferencia'),
            ('Tarjeta Crédito', 'Tarjeta de Crédito'),
            ('Tarjeta Débito', 'Tarjeta de Débito'),
            ('Efectivo', 'Efectivo'),
            ('Crédito Empresa', 'Crédito Empresa'),
        ],
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    fecha_emision = forms.DateField(
        label="Fecha de Emisión",
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )

    fecha_vencimiento = forms.DateField(
        label="Fecha de Vencimiento",
        required=False,  
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
)

    def clean_rut(self):
        rut = self.cleaned_data.get('rut', '').replace('.', '').replace('-', '')
        if len(rut) < 8 or not rut[:-1].isdigit():
            raise forms.ValidationError("El RUT ingresado no es válido.")
        return rut

    def clean_fecha_vencimiento(self):
        fecha_emision = self.cleaned_data.get('fecha_emision')
        fecha_vencimiento = self.cleaned_data.get('fecha_vencimiento')
        if fecha_emision and fecha_vencimiento and fecha_vencimiento < fecha_emision:
            raise forms.ValidationError("La fecha de vencimiento debe ser posterior a la de emisión.")
        return fecha_vencimiento