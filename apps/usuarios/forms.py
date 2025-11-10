from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario

class CrearUsuarioForm(UserCreationForm):
    telefono = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': '+56 9 1234 5678',
            'pattern': r'\+56\s9\s\d{4}\s\d{4}',
            'title': 'Formato: +56 9 1234 5678'
        })
    )
    
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'rol', 'telefono', 'password1', 'password2']

    def clean_rol(self):
        rol = self.cleaned_data.get('rol')
        if rol not in ['Vendedor', 'Tesoreria']:
            raise forms.ValidationError("Solo se pueden crear usuarios con rol Vendedor o Tesorería.")
        return rol
    
    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        if telefono:
            telefono_limpio = telefono.replace(' ', '')
            if not telefono_limpio.startswith('+569') or len(telefono_limpio) != 12:
                raise forms.ValidationError("El teléfono debe tener formato chileno: +56 9 1234 5678")
        return telefono


class EditarUsuarioForm(forms.ModelForm):
    telefono = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': '+56 9 1234 5678',
            'pattern': r'\+56\s9\s\d{4}\s\d{4}',
            'title': 'Formato: +56 9 1234 5678'
        })
    )
    
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'rol', 'telefono', 'is_active']
    
    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        if telefono:
            telefono_limpio = telefono.replace(' ', '')
            if not telefono_limpio.startswith('+569') or len(telefono_limpio) != 12:
                raise forms.ValidationError("El teléfono debe tener formato chileno: +56 9 1234 5678")
        return telefono