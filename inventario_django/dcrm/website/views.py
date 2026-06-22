import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, Avg
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.http import JsonResponse, HttpResponseNotAllowed
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils import timezone

from .forms import RegistroForm, JornadaForm
from .models import Registro, Jornada, Inscripcion


# ---------------------------------------------------------------------------
# Mixins de control de acceso
# ---------------------------------------------------------------------------

class OrgAdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Restringe el acceso a usuarios con rol ADMIN u ORGANIZADOR.
    Responde con JSON 403 para peticiones AJAX, o redirige a home para el resto.
    """

    def test_func(self):
        u = self.request.user
        return u.is_superuser or u.groups.filter(name__in=['ADMIN', 'ORGANIZADOR']).exists()

    def handle_no_permission(self):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(
                {'success': False, 'message': 'No tienes permisos suficientes para acceder a esta sección.'},
                status=403
            )
        messages.error(self.request, 'No tienes permisos suficientes para acceder a esta sección.')
        return redirect('home')


def _es_admin_o_organizador(user):
    """Helper para verificar rol ADMIN/ORGANIZADOR desde funciones."""
    return user.is_superuser or user.groups.filter(name__in=['ADMIN', 'ORGANIZADOR']).exists()


# ---------------------------------------------------------------------------
# Vistas de Jornadas — Gestión (ADMIN / ORGANIZADOR)
# ---------------------------------------------------------------------------

@method_decorator(ensure_csrf_cookie, name='dispatch')
class JornadaListView(OrgAdminRequiredMixin, ListView):
    """Listado de jornadas con soporte AJAX."""
    model = Jornada
    template_name = 'jornada_home.html'
    context_object_name = 'jornadas'
    paginate_by = 10

    def get_queryset(self):
        return Jornada.objects.all().select_related('id_organizador').order_by('-fecha')

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            self.object_list = self.get_queryset()
            context = self.get_context_data()
            html = render_to_string('partials/jornada_list.html', context, request=request)
            return JsonResponse({'success': True, 'html': html})
        return super().get(request, *args, **kwargs)


class JornadaCreateView(OrgAdminRequiredMixin, CreateView):
    """Crear jornada con soporte AJAX."""
    model = Jornada
    form_class = JornadaForm
    template_name = 'partials/jornada_form.html'

    def form_valid(self, form):
        jornada = form.save()
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Recargar listado tras creación exitosa
            jornadas = Jornada.objects.all().select_related('id_organizador').order_by('-fecha')
            lista_html = render_to_string(
                'partials/jornada_list.html',
                {'jornadas': jornadas},
                request=self.request
            )
            return JsonResponse({
                'success': True,
                'message': 'Jornada creada exitosamente.',
                'toast_category': 'success',
                'html': lista_html,
            })
        messages.success(self.request, 'Jornada creada exitosamente.')
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            html = render_to_string('partials/jornada_form.html', {'form': form}, request=self.request)
            return JsonResponse({
                'success': False,
                'message': 'Por favor corrige los errores del formulario.',
                'toast_category': 'danger',
                'html': html,
            })
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('jornada_list')


class JornadaUpdateView(OrgAdminRequiredMixin, UpdateView):
    """Editar jornada — solo jornadas en estado 'pendiente'."""
    model = Jornada
    form_class = JornadaForm
    template_name = 'partials/jornada_form.html'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.estado != 'pendiente':
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                raise PermissionDenied('Solo se pueden editar jornadas en estado pendiente.')
            raise PermissionDenied('Solo se pueden editar jornadas en estado pendiente.')
        return obj

    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except PermissionDenied as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse(
                    {'success': False, 'message': str(e), 'toast_category': 'warning'},
                    status=403
                )
            messages.error(request, str(e))
            return redirect('jornada_list')

    def form_valid(self, form):
        # RN1.1.3 — publicar requiere organizador asignado
        nueva_estado = form.cleaned_data.get('estado')
        nuevo_organizador = form.cleaned_data.get('id_organizador')
        if nueva_estado == 'activa' and not nuevo_organizador:
            form.add_error(
                'id_organizador',
                'La jornada debe tener al menos un organizador antes de publicarse.'
            )
            return self.form_invalid(form)

        form.save()
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            jornadas = Jornada.objects.all().select_related('id_organizador').order_by('-fecha')
            lista_html = render_to_string(
                'partials/jornada_list.html',
                {'jornadas': jornadas},
                request=self.request
            )
            return JsonResponse({
                'success': True,
                'message': 'Jornada actualizada exitosamente.',
                'toast_category': 'success',
                'html': lista_html,
            })
        messages.success(self.request, 'Jornada actualizada exitosamente.')
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            html = render_to_string('partials/jornada_form.html', {'form': form, 'object': self.object}, request=self.request)
            return JsonResponse({
                'success': False,
                'message': 'Por favor corrige los errores del formulario.',
                'toast_category': 'danger',
                'html': html,
            })
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('jornada_list')


class JornadaDeleteView(OrgAdminRequiredMixin, View):
    """
    Cancelación lógica de jornada (estado → 'cancelada').
    Solo jornadas en estado 'pendiente' pueden cancelarse.
    GET: muestra partial de confirmación (con alerta si >50% cupo inscrito).
    POST: ejecuta la cancelación lógica.
    """

    def _get_jornada(self, pk):
        jornada = get_object_or_404(Jornada, pk=pk)
        if jornada.estado != 'pendiente':
            raise PermissionDenied('Solo se pueden cancelar jornadas en estado pendiente.')
        return jornada

    def get(self, request, pk):
        try:
            jornada = self._get_jornada(pk)
        except PermissionDenied as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse(
                    {'success': False, 'message': str(e), 'toast_category': 'warning'},
                    status=403
                )
            messages.warning(request, str(e))
            return redirect('jornada_list')

        advertencia_cupo = jornada.porcentaje_inscripcion > 50

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            html = render_to_string(
                'partials/jornada_confirm_delete.html',
                {'object': jornada, 'advertencia_cupo': advertencia_cupo},
                request=request
            )
            return JsonResponse({'success': True, 'html': html})

        return render(request, 'partials/jornada_confirm_delete.html', {
            'object': jornada,
            'advertencia_cupo': advertencia_cupo,
        })

    def post(self, request, pk):
        try:
            jornada = self._get_jornada(pk)
        except PermissionDenied as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse(
                    {'success': False, 'message': str(e), 'toast_category': 'warning'},
                    status=403
                )
            messages.warning(request, str(e))
            return redirect('jornada_list')

        jornada.estado = 'cancelada'
        jornada.save(update_fields=['estado', 'fecha_actualizacion'])

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            jornadas = Jornada.objects.all().select_related('id_organizador').order_by('-fecha')
            lista_html = render_to_string(
                'partials/jornada_list.html',
                {'jornadas': jornadas},
                request=request
            )
            return JsonResponse({
                'success': True,
                'message': 'Jornada cancelada exitosamente.',
                'toast_category': 'success',
                'html': lista_html,
            })
        messages.success(request, 'Jornada cancelada exitosamente.')
        return redirect('jornada_list')


# ---------------------------------------------------------------------------
# Vistas de Jornadas — Residente
# ---------------------------------------------------------------------------

class JornadaDisponiblesView(LoginRequiredMixin, ListView):
    """
    Listado de jornadas activas y con fecha vigente.
    Residentes ven solo las de su barrio; ADMIN/ORGANIZADOR ven todas.
    """
    model = Jornada
    template_name = 'jornada_disponibles.html'
    context_object_name = 'jornadas'

    def get_queryset(self):
        qs = Jornada.objects.filter(
            estado='activa',
            fecha__gte=timezone.now()
        ).select_related('id_organizador').order_by('fecha')

        user = self.request.user
        if not _es_admin_o_organizador(user):
            try:
                barrio = user.registro.barrio
                if barrio:
                    qs = qs.filter(barrio__iexact=barrio)
                else:
                    qs = qs.none()
            except Registro.DoesNotExist:
                qs = qs.none()

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        # IDs de jornadas en que el usuario ya está inscrito
        if user.is_authenticated:
            context['inscripciones_ids'] = set(
                Inscripcion.objects.filter(residente=user).values_list('jornada_id', flat=True)
            )
        else:
            context['inscripciones_ids'] = set()
        return context


@login_required
def inscribir_jornada(request, pk):
    """
    POST — Inscribe al usuario autenticado en una jornada activa.
    Valida: cupo disponible, no duplicado, estado activa.
    """
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    jornada = get_object_or_404(Jornada, pk=pk)

    if jornada.estado != 'activa':
        return JsonResponse({
            'success': False,
            'message': 'Esta jornada no está disponible para inscripciones.',
            'toast_category': 'danger',
        })

    if Inscripcion.objects.filter(residente=request.user, jornada=jornada).exists():
        return JsonResponse({
            'success': False,
            'message': 'Ya estás inscrito en esta jornada.',
            'toast_category': 'warning',
        })

    if not jornada.cupo_disponible:
        return JsonResponse({
            'success': False,
            'message': 'Esta jornada no tiene cupo disponible.',
            'toast_category': 'danger',
        })

    Inscripcion.objects.create(residente=request.user, jornada=jornada)
    return JsonResponse({
        'success': True,
        'message': '¡Inscripción realizada exitosamente!',
        'toast_category': 'success',
    })


class MisInscripcionesView(LoginRequiredMixin, ListView):
    """Listado de inscripciones del usuario autenticado."""
    model = Inscripcion
    template_name = 'mis_inscripciones.html'
    context_object_name = 'inscripciones'

    def get_queryset(self):
        return Inscripcion.objects.filter(
            residente=self.request.user
        ).select_related('jornada').order_by('-fecha_inscripcion')


class AsistenciaRegistrarView(OrgAdminRequiredMixin, View):
    """
    GET:  muestra lista de inscritos de una jornada para marcar asistencia.
    POST: actualiza asistencia=True para los IDs enviados.
    """

    def get(self, request):
        jornada_id = request.GET.get('jornada_id')
        jornada = get_object_or_404(Jornada, pk=jornada_id) if jornada_id else None
        jornadas = Jornada.objects.filter(
            estado__in=['activa', 'finalizada']
        ).order_by('-fecha')
        inscripciones = jornada.inscripciones.select_related('residente').all() if jornada else []

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            html = render_to_string(
                'asistencia.html',
                {'jornada': jornada, 'inscripciones': inscripciones, 'jornadas': jornadas},
                request=request
            )
            return JsonResponse({'success': True, 'html': html})

        return render(request, 'asistencia.html', {
            'jornada': jornada,
            'inscripciones': inscripciones,
            'jornadas': jornadas,
        })

    def post(self, request):
        jornada_id = request.POST.get('jornada_id')
        ids_confirmados = request.POST.getlist('inscritos_confirmados')

        if not jornada_id:
            return JsonResponse({
                'success': False,
                'message': 'Jornada no especificada.',
                'toast_category': 'danger',
            })

        # Marcar como NO asistió todos los de la jornada, luego marcar los confirmados
        Inscripcion.objects.filter(jornada_id=jornada_id).update(asistencia=False, confirmada=False)
        if ids_confirmados:
            Inscripcion.objects.filter(
                pk__in=ids_confirmados, jornada_id=jornada_id
            ).update(asistencia=True, confirmada=True)

        return JsonResponse({
            'success': True,
            'message': f'Asistencia registrada para {len(ids_confirmados)} participante(s).',
            'toast_category': 'success',
        })


class ReportesView(OrgAdminRequiredMixin, TemplateView):
    """Vista de reportes y métricas (solo ADMIN/ORGANIZADOR)."""
    template_name = 'reportes.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Conteo de jornadas por estado
        context['jornadas_por_estado'] = (
            Jornada.objects.values('estado')
            .annotate(total=Count('id'))
            .order_by('estado')
        )

        # Top 5 jornadas con más inscritos
        context['top_jornadas'] = (
            Jornada.objects.annotate(num_inscritos=Count('inscripciones'))
            .order_by('-num_inscritos')[:5]
        )

        # Porcentaje de asistencia promedio (sobre inscripciones confirmadas)
        total_inscritos = Inscripcion.objects.count()
        total_asistieron = Inscripcion.objects.filter(asistencia=True).count()
        context['pct_asistencia'] = (
            round((total_asistieron / total_inscritos) * 100, 1) if total_inscritos > 0 else 0
        )
        context['total_inscritos'] = total_inscritos
        context['total_asistieron'] = total_asistieron

        # Totales generales
        context['total_jornadas'] = Jornada.objects.count()

        return context


# ---------------------------------------------------------------------------
# Vistas generales (sin cambios funcionales, solo consolidadas)
# ---------------------------------------------------------------------------

@ensure_csrf_cookie
def home(request):
    """Vista principal."""
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
    return render(request, 'home.html')


def registro_view(request):
    """Vista para el registro de nuevos usuarios."""
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
            messages.success(request, '¡Registro exitoso! Por favor inicia sesión.')
            return redirect('home')
        messages.error(request, 'Por favor corrige los errores abajo.')
    else:
        form = RegistroForm()

    return render(request, 'registro.html', {'form': form})


def login_view(request):
    """Vista para iniciar sesión."""
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
        messages.error(request, 'Nombre de usuario o contraseña incorrectos.')
        return redirect('home')

    return redirect('home')


@login_required
def logout_view(request):
    """Vista para cerrar sesión."""
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
    return render(request, 'edit_record.html', {'user': user, 'registro': registro})


def add_record(request):
    form = RegistroForm(request.POST or None)
    if request.user.is_authenticated:
        if request.method == 'POST':
            if form.is_valid():
                add = form.save()
                messages.success(request, f'¡Usuario {add.username} creado exitosamente!')
                return redirect('home')
        return render(request, 'add_record.html', {'form': form})
    messages.error(request, 'Debes iniciar sesión para agregar un nuevo usuario.')
    return redirect('home')


@login_required
def delete_record(request, record_id):
    """Vista para eliminar un registro."""
    if request.method == 'POST':
        registro = get_object_or_404(Registro, id=record_id)
        registro.delete()
        messages.success(request, 'Registro eliminado exitosamente.')
    else:
        messages.error(request, 'Método no permitido para eliminar un registro.')
    return redirect('home')
