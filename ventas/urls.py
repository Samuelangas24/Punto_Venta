from django.urls import path
from .views import (
    reporte_ventas, buscar_producto, crear_venta_page, guardar_venta,
    generar_recibo_venta, api_estadisticas_hoy, corte_caja, abrir_corte, cerrar_corte, generar_pdf_corte,
    consultar_inventario, api_inventario,
    almacen_admin, api_almacen_buscar, guardar_producto_almacen, eliminar_producto_almacen,
    actualizar_cantidad_almacen, actualizar_precio_almacen, actualizar_descripcion_almacen
)

urlpatterns = [
    path('reporte/', reporte_ventas, name='reporte_ventas'),
    path('buscar/', buscar_producto, name='buscar_producto'),
    path('crear/', crear_venta_page, name='crear_venta'),
    path('guardar/', guardar_venta, name='guardar_venta'),
    path('stats/', api_estadisticas_hoy, name='api_estadisticas_hoy'),
    path('corte/', corte_caja, name='corte_caja'),
    path('corte/abrir/', abrir_corte, name='abrir_corte'),
    path('corte/cerrar/', cerrar_corte, name='cerrar_corte'),
    path('recibo/<int:venta_id>/', generar_recibo_venta, name='generar_recibo_venta'),
    path('corte/pdf/<int:corte_id>/', generar_pdf_corte, name='generar_pdf_corte'),
    path('inventario/', consultar_inventario, name='consultar_inventario'),
    path('inventario/buscar/', api_inventario, name='api_inventario'),
    path('almacen/', almacen_admin, name='almacen_admin'),
    path('almacen/buscar/', api_almacen_buscar, name='api_almacen_buscar'),
    path('almacen/guardar/', guardar_producto_almacen, name='guardar_producto_almacen'),
    path('almacen/eliminar/', eliminar_producto_almacen, name='eliminar_producto_almacen'),
    path('almacen/actualizar-cantidad/', actualizar_cantidad_almacen, name='actualizar_cantidad_almacen'),
    path('almacen/actualizar-precio/', actualizar_precio_almacen, name='actualizar_precio_almacen'),
    path('almacen/actualizar-descripcion/', actualizar_descripcion_almacen, name='actualizar_descripcion_almacen'),
]
