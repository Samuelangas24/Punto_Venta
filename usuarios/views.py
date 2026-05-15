from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from .forms import LoginForm

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
    }
    return render(request, 'punto_de_venta.html', context)