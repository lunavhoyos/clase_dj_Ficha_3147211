import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .forms import RegistroForm, JornadaForm
from .models import Registro, Jornada


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin para restringir acceso únicamente a usuarios con rol ADMIN"""
    
    def test_func(self):
        return self.request.user.groups.filter(name='ADMIN').exists() or self.request.user.is_superuser
    
    def handle_no_permission(self):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'Acceso denegado. Se requiere rol ADMIN.',
                'html': render_to_string('partials/toast_alert.html', {
                    'message': 'Acceso denegado. Se requiere rol ADMIN.',
                    'category': 'danger'
                })
            }, status=403)
        messages.error(self.request, 'Acceso denegado. Se requiere rol ADMIN.')
        return redirect('home')


class JornadaListView(AdminRequiredMixin, ListView):
    """Listado de jornadas con soporte AJAX"""
    model = Jornada
    template_name = 'partials/jornada_list.html'
    context_object_name = 'jornadas'
    paginate_by = 10

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            self.object_list = self.get_queryset()
            context = self.get_context_data()
            html = render_to_string('partials/jornada_list.html', context, request=request)
            return JsonResponse({'success': True, 'html': html})
        return super().get(request, *args, **kwargs)


class JornadaCreateView(AdminRequiredMixin, CreateView):
    """Crear jornada con soporte AJAX"""
    model = Jornada
    form_class = JornadaForm
    template_name = 'partials/jornada_form.html'

    def form_valid(self, form):
        form.save()
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Jornada creada exitosamente.',
                'html': render_to_string('partials/toast_alert.html', {
                    'message': 'Jornada creada exitosamente.',
                    'category': 'success'
                })
            })
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            html = render_to_string('partials/jornada_form.html', {'form': form}, request=self.request)
            return JsonResponse({'success': False, 'html': html, 'message': 'Error al crear la jornada.'})
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('jornada_list')


class JornadaUpdateView(AdminRequiredMixin, UpdateView):
    """Editar jornada con soporte AJAX"""
    model = Jornada
    form_class = JornadaForm
    template_name = 'partials/jornada_form.html'

    def form_valid(self, form):
        form.save()
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Jornada actualizada exitosamente.',
                'html': render_to_string('partials/toast_alert.html', {
                    'message': 'Jornada actualizada exitosamente.',
                    'category': 'success'
                })
            })
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            html = render_to_string('partials/jornada_form.html', {'form': form}, request=self.request)
            return JsonResponse({'success': False, 'html': html, 'message': 'Error al actualizar la jornada.'})
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('jornada_list')


class JornadaDeleteView(AdminRequiredMixin, DeleteView):
    """Eliminar jornada con soporte AJAX"""
    model = Jornada
    template_name = 'partials/jornada_confirm_delete.html'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            self.object.delete()
            return JsonResponse({
                'success': True,
                'message': 'Jornada eliminada exitosamente.',
                'html': render_to_string('partials/toast_alert.html', {
                    'message': 'Jornada eliminada exitosamente.',
                    'category': 'success'
                })
            })
        return self.delete(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('jornada_list')


def home(request):
    """Vista principal - muestra el formulario de registro si no está autenticado"""
    if request.user.is_authenticated:
        registros_list = Registro.objects.all().select_related('user')
        paginator = Paginator(registros_list, 10)
        page_number = request.GET.get('page')
        registros = paginator.get_page(page_number)
        return render(request, 'home.html', {
            'user': request.user,
            'registros': registros,
            'page_obj': registros,
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
