from django.db import models

from apps.usuarios.models import Usuario  # <--- IMPORTACIÓN AÑADIDA

class Cliente(models.Model):
    # --- CAMPO AÑADIDO ---
    # Esta es la conexión clave con el modelo Usuario
    user = models.OneToOneField(
        Usuario, 
        on_delete=models.CASCADE, 
        related_name='perfil_cliente',
        null=True,  # <--- AÑADE ESTO
        blank=True  # <--- Y AÑADE ESTO
    )
    # ---------------------
    
    rut = models.CharField(max_length=12, unique=True)
    razon_social = models.CharField(max_length=255)
    giro = models.CharField(max_length=255, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    email_facturacion = models.EmailField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.razon_social} ({self.rut})"
    
    class Meta:
        db_table = 'clientes'
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'


class Proveedor(models.Model):
    rut = models.CharField(max_length=12, unique=True)
    razon_social = models.CharField(max_length=255)
    email_contacto = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    
    def __str__(self):
        return self.razon_social
    
    class Meta:
        db_table = 'proveedores'
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'