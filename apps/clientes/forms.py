from django import forms
from .models import Proveedor, Cliente
from django.core.exceptions import ValidationError

# --- FUNCIÓN CENTRAL DE VALIDACIÓN DE RUT ---
def validar_rut(rut_completo):
    """
    Verifica que el RUT sea válido (formato y dígito verificador).
    """
    rut_completo = rut_completo.upper().replace(".", "").replace("-", "")
    if not rut_completo:
        raise ValidationError("El campo RUT es obligatorio.")

    if not all(c.isalnum() for c in rut_completo):
        raise ValidationError("El RUT solo puede contener números y la letra 'K'.")

    # Separar cuerpo y dígito verificador (DV)
    cuerpo = rut_completo[:-1]
    dv = rut_completo[-1]
    
    # El cuerpo debe ser numérico
    if not cuerpo.isdigit():
        raise ValidationError("El cuerpo del RUT debe ser numérico.")

    # Calcular dígito verificador esperado (Algoritmo Módulo 11)
    try:
        reverso = cuerpo[::-1]
        multiplicador = 2
        suma = 0
        for c in reverso:
            suma += int(c) * multiplicador
            multiplicador = multiplicador + 1 if multiplicador < 7 else 2
        
        dv_calculado = 11 - (suma % 11)

        if dv_calculado == 11:
            dv_final = '0'
        elif dv_calculado == 10:
            dv_final = 'K'
        else:
            dv_final = str(dv_calculado)
        
        if dv_final != dv:
            raise ValidationError("El dígito verificador es incorrecto.")
            
    except Exception:
        raise ValidationError("Formato de RUT inválido. Ej: 12345678-K")

    return rut_completo # Devuelve el RUT limpio


# ====================================================================
# FORMS (SE APLICAN LAS VALIDACIONES)
# ====================================================================

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['rut', 'razon_social', 'email_contacto', 'telefono']
        widgets = {
            'rut': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 76.123.456-K'}),
            'razon_social': forms.TextInput(attrs={'class': 'form-control'}),
            'email_contacto': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_rut(self):
        """Aplica la validación de RUT al campo del formulario."""
        rut = self.cleaned_data.get('rut')
        return validar_rut(rut) # Llama a la función externa


class ClienteForm(forms.ModelForm):
    """
    Formulario para crear un Cliente desde el modal.
    """
    class Meta:
        model = Cliente
        fields = ['rut', 'razon_social', 'giro', 'direccion', 'email_facturacion']
        widgets = {
            'rut': forms.TextInput(attrs={'class': 'form-control', 'required': True, 'placeholder': 'Ej: 12.345.678-9'}),
            'razon_social': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'giro': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'email_facturacion': forms.EmailInput(attrs={'class': 'form-control'}),
        }
    
    def clean_rut(self):
        """Aplica la validación de RUT al campo del formulario."""
        rut = self.cleaned_data.get('rut')
        return validar_rut(rut) # Llama a la función externa


class CompletarPerfilForm(forms.ModelForm):
    """
    Formulario para que el CLIENTE complete su perfil por primera vez.
    """
    class Meta:
        model = Cliente
        fields = ['razon_social', 'rut', 'giro', 'direccion', 'email_facturacion']
        widgets = {
            'razon_social': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tu nombre completo o razón social'}),
            'rut': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 12.345.678-9'}),
            'giro': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Venta de productos...'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Tu dirección completa'}),
            'email_facturacion': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@facturacion.cl'}),
        }
        labels = {
            'razon_social': 'Nombre Completo o Razón Social',
            'rut': 'RUT',
            'giro': 'Giro (Opcional)',
            'direccion': 'Dirección de Despacho/Facturación',
            'email_facturacion': 'Email para Facturación',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['razon_social'].required = True
        self.fields['rut'].required = True
        self.fields['direccion'].required = True
        self.fields['email_facturacion'].required = True

    def clean_rut(self):
        """Aplica la validación de RUT al campo del formulario."""
        rut = self.cleaned_data.get('rut')
        return validar_rut(rut) # Llama a la función externa