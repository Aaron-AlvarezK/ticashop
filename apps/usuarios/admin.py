from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

class UsuarioAdmin(UserAdmin):
    model = Usuario
    # TEMPORAL: Quitar 'cliente' de list_display hasta que arreglemos el modelo
    list_display = ['username', 'email', 'rol', 'activo', 'date_joined']
    list_filter = ['rol', 'activo', 'date_joined']
    fieldsets = UserAdmin.fieldsets + (
        ('Información TicaShop', {
            'fields': ('rol', 'telefono', 'activo')  # Quitar 'cliente' temporalmente
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información TicaShop', {
            'fields': ('rol', 'telefono', 'activo')  # Quitar 'cliente' temporalmente
        }),
    )

admin.site.register(Usuario, UsuarioAdmin)