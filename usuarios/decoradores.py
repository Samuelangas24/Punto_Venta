# decoradores de permisos por rol

from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import redirect

def rol_requerido(*roles):
    """Decorador para requerir un rol específico"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            # Si el usuario es admin, siempre tiene acceso
            if request.user.rol == 'admin':
                return view_func(request, *args, **kwargs)
            
            # Si no es admin, verificar si tiene el rol requerido
            if request.user.rol in roles:
                return view_func(request, *args, **kwargs)
            
            return HttpResponseForbidden("No tienes permisos para acceder a esta página")
        return wrapper
    return decorator

def solo_activos(view_func):
    """Decorador para solo usuarios activos"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.activo:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper
