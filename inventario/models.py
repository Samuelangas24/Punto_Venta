# inventario/models.py

from django.db import models
from django.contrib.auth.models import User

class Sucursal(models.Model):
    nombre = models.CharField(max_length=100)
    ubicacion = models.CharField(max_length=200)

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    codigo_barras = models.CharField(max_length=50, blank=True, null=True, unique=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.nombre} (${self.precio_venta})"

class InventarioSucursal(models.Model):
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField(default=0)

    class Meta:
        unique_together = ('sucursal', 'producto') # Evita duplicados