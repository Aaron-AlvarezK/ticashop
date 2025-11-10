from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    ROLES = (
        ('Administrador', 'Administrador'),
        ('Vendedor', 'Vendedor'),
        ('Tesoreria', 'Tesorería'),
        ('Cliente', 'Cliente'),
    )
    
    rol = models.CharField(max_length=13, choices=ROLES, default='Cliente')
    telefono = models.CharField(max_length=20, blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Si es superuser y no tiene rol asignado, asignar Administrador
        if self.is_superuser and self.rol == 'Cliente':
            self.rol = 'Administrador'
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.username} - {self.rol}"
    
    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'