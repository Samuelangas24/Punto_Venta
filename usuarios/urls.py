from django.urls import path
from .views import (
    login_view, 
    punto_de_venta_view, 
    inicio_view,
    admin_panel,
    crear_usuario,
    listar_usuarios,
    editar_usuario,
    eliminar_usuario,
)

urlpatterns = [
    path('', inicio_view, name='inicio'),
    path('login/', login_view, name='login'),
    path('punto-de-venta/', punto_de_venta_view, name='punto_de_venta'),
    
    # Rutas de administración personalizada
    path('configuracion/', admin_panel, name='configuracion'),
    path('configuracion/panel/', admin_panel, name='admin_panel'),
    path('configuracion/usuarios/crear/', crear_usuario, name='crear_usuario'),
    path('configuracion/usuarios/', listar_usuarios, name='listar_usuarios'),
    path('configuracion/usuarios/<int:usuario_id>/editar/', editar_usuario, name='editar_usuario'),
    path('configuracion/usuarios/<int:usuario_id>/eliminar/', eliminar_usuario, name='eliminar_usuario'),
]
