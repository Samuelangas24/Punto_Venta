from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import LoginForm, CrearUsuarioForm
from inventario.models import Sucursal

User = get_user_model()

def inicio_view(request):
    """Página de inicio"""
    if request.user.is_authenticated:
        return redirect('punto_de_venta')
    return render(request, 'inicio.html')

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                username=form.cleaned_data['usuario'], 
                password=form.cleaned_data['password']
            )
            if user:
                login(request, user)
                # GUARDAMOS LA SUCURSAL EN LA SESIÓN
                request.session['sucursal_id'] = form.cleaned_data['sucursal'].id
                request.session['sucursal_nombre'] = form.cleaned_data['sucursal'].nombre
                
                # Siempre redirige al punto de venta; el admin accede a configuración desde el menú
                return redirect('punto_de_venta') # Te manda a la caja
    else:
        form = LoginForm()
    
    return render(request, 'login.html', {'form': form})


@login_required(login_url='login')
def punto_de_venta_view(request):
    """Vista del punto de venta/dashboard"""
    sucursal = request.session.get('sucursal_nombre', 'Sucursal')
    context = {
        'sucursal': sucursal,
        'usuario': request.user.username,
        'user': request.user,
        'rol': request.user.rol,
    }
    return render(request, 'punto_de_venta.html', context)


def es_administrador(user):
    """Verifica si es administrador"""
    return user.is_superuser


@login_required(login_url='login')
@user_passes_test(es_administrador, login_url='punto_de_venta')
def admin_panel(request):
    """Panel de administración personalizado"""
    usuarios = User.objects.all().order_by('-date_joined')
    sucursales = Sucursal.objects.all()
    
    context = {
        'usuarios': usuarios,
        'sucursales': sucursales,
        'total_usuarios': usuarios.count(),
        'total_sucursales': sucursales.count(),
    }
    return render(request, 'admin/panel.html', context)


@login_required(login_url='login')
@user_passes_test(es_administrador, login_url='punto_de_venta')
def crear_usuario(request):
    """Crear nuevo usuario"""
    if request.method == 'POST':
        form = CrearUsuarioForm(request.POST)
        if form.is_valid():
            # Crear usuario
            usuario = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['nombre_completo'],
                is_staff=form.cleaned_data['es_administrador'],
                is_superuser=form.cleaned_data['es_administrador'],
            )
            return redirect('admin_panel')
    else:
        form = CrearUsuarioForm()
    
    context = {'form': form}
    return render(request, 'admin/crear_usuario.html', context)


@login_required(login_url='login')
@user_passes_test(es_administrador, login_url='punto_de_venta')
def listar_usuarios(request):
    """Listar todos los usuarios"""
    usuarios = User.objects.all().order_by('-date_joined')
    context = {'usuarios': usuarios}
    return render(request, 'admin/listar_usuarios.html', context)


@login_required(login_url='login')
@user_passes_test(es_administrador, login_url='punto_de_venta')
def editar_usuario(request, usuario_id):
    """Editar usuario"""
    usuario = User.objects.get(id=usuario_id)
    
    if request.method == 'POST':
        usuario.first_name = request.POST.get('nombre_completo', usuario.first_name)
        usuario.email = request.POST.get('email', usuario.email)
        
        # Si se ingresa nueva contraseña
        password = request.POST.get('password')
        if password:
            usuario.set_password(password)
        
        usuario.is_superuser = 'es_administrador' in request.POST
        usuario.is_staff = usuario.is_superuser
        usuario.save()
        
        return redirect('listar_usuarios')
    
    context = {'usuario': usuario}
    return render(request, 'admin/editar_usuario.html', context)


@login_required(login_url='login')
@user_passes_test(es_administrador, login_url='punto_de_venta')
def eliminar_usuario(request, usuario_id):
    """Eliminar usuario"""
    usuario = User.objects.get(id=usuario_id)
    
    if request.method == 'POST':
        usuario.delete()
        return redirect('listar_usuarios')
    
    context = {'usuario': usuario}
    return render(request, 'admin/eliminar_usuario.html', context)