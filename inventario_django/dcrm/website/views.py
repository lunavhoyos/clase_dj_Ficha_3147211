from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegistroForm
from .models import Registro

def home(request):
    """Vista principal - muestra el formulario de registro si no está autenticado"""
    if request.user.is_authenticated:
        # Obtener todos los registros para mostrar en el listado
        registros = Registro.objects.all().select_related('user')
        return render(request, 'home.html', {
            'user': request.user,
            'registros': registros
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

@login_required
def edit_record(request, record_id):
    registro = get_object_or_404(Registro, id=record_id)
    user = registro.user
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()
        registro.telefono = request.POST.get('telefono', '')
        registro.direccion = request.POST.get('direccion', '')
        registro.ciudad = request.POST.get('ciudad', '')
        registro.save()
        messages.success(request, 'Registro actualizado exitosamente.')
        return redirect('home')
    return render(request, 'edit_record.html', {
        'user': user,
        'registro': registro,
    })

#Esta parte para crear la trajeta de crear usuario
def add_record(request):
    form = RegistroForm(request.POST or None)
    if request.user.is_authenticated:
        if request.method == 'POST':
            if form.is_valid():
                add = form.save()
                messages.success(request, f'¡Usuario {add.username} creado exitosamente!')
                return redirect('home')
        return render(request, 'add_record.html', {'form': form})
    else:
        messages.error(request, 'Debes iniciar sesión para agregar un nuevo usuario.')
        return redirect('home')

@login_required
def delete_record(request, record_id):
    """Vista para eliminar un registro"""
    if request.method == 'POST':
        registro = get_object_or_404(Registro, id=record_id)
        registro.delete()
        messages.success(request, 'Registro eliminado exitosamente.')
    else:
        messages.error(request, 'Método no permitido para eliminar un registro.')
    return redirect('home')
