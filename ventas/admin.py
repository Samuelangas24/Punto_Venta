from django.contrib import admin
from .models import Venta, DetalleVenta

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'sucursal', 'usuario', 'fecha', 'total')
    list_filter = ('fecha', 'sucursal')
    search_fields = ('id', 'usuario__username')

@admin.register(DetalleVenta)
class DetalleVentaAdmin(admin.ModelAdmin):
    list_display = ('venta', 'producto', 'cantidad', 'precio_unitario', 'subtotal')
