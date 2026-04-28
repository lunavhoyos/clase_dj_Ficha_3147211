from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegistroForm

def home(request):
    """Vista principal - muestra el formulario de registro si no está autenticado"""
    if request.user.is_authenticated:
        return render(request, 'home.html', {
            'user': request.user
        })
    else:
        return render(request, 'home.html')

def registro_view(request):
    """Vista para el registro de nuevos usuarios"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Iniciar sesión automáticamente después del registro
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            if user is not None:
                login(request, user)
                messages.success(request, f'¡Bienvenido/a {user.first_name}! Tu cuenta ha sido creada exitosamente.')
                return redirect('home')
            else:
                messages.success(request, f'¡Registro exitoso! Por favor inicia sesión.')
                return redirect('home')
        else:
            messages.error(request, 'Por favor corrige los errores abajo.')
    else:
        form = RegistroForm()
    
    return render(request, 'registro.html', {'form': form})

def login_view(request):
    """Vista para iniciar sesión"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'¡Bienvenido/a de vuelta, {user.username}!')
            return redirect('home')
        else:
            messages.error(request, 'Nombre de usuario o contraseña incorrectos.')
            return redirect('home')
    
    return redirect('home')

@login_required
def logout_view(request):
    """Vista para cerrar sesión"""
    logout(request)
    messages.info(request, 'Has cerrado sesión exitosamente.')
    return redirect('home')
