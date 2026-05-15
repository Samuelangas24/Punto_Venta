from django.contrib.auth.models import AbstractUser
from django.db import models
from inventario.models import Sucursal

class UsuarioPersonalizado(AbstractUser):
    # Definimos los roles
    ROL_CHOICES = (
        ('admin', 'Administrador'),
        ('vendedor', 'Vendedor'),
        ('cajero', 'Cajero'),
    )
    rol = models.CharField(max_length=10, choices=ROL_CHOICES, default='vendedor')
    sucursal = models.ForeignKey(Sucursal, on_delete=models.SET_NULL, null=True, blank=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.username} ({self.get_rol_display()})"
    
    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
    