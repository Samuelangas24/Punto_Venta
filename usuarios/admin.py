from django.contrib import admin
from .models import UsuarioPersonalizado

@admin.register(UsuarioPersonalizado)
class UsuarioPersonalizadoAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'rol', 'sucursal')
    
     