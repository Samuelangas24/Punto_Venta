from django.urls import path
from .views import login_view, punto_de_venta_view, inicio_view

urlpatterns = [
    path('', inicio_view, name='inicio'),
    path('login/', login_view, name='login'),
    path('punto-de-venta/', punto_de_venta_view, name='punto_de_venta'),
]
