# inventario/admin.py
from django.contrib import admin
from .models import Sucursal, Producto, InventarioSucursal

@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ubicacion') # Columnas que verás en la tabla

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo_barras', 'precio_venta')

@admin.register(InventarioSucursal)
class InventarioSucursalAdmin(admin.ModelAdmin):
    list_display = ('sucursal', 'producto', 'cantidad')
