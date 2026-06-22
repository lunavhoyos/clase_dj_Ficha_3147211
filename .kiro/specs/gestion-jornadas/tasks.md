# Implementation Plan

## Overview

Plan de implementación para el módulo de Gestión de Jornadas de Recolección. Las tareas están ordenadas de menor a mayor dependencia: primero la capa de backend (modelos, vistas, URLs), luego la capa de presentación (templates, JS), y finalmente la verificación integral.

## Tasks

- [x] 1. Crear context processor de roles
  - Crear el archivo `website/context_processors.py` con la función `user_rol(request)` que devuelve `{'user_rol': 'ADMIN'|'ORGANIZADOR'|'RESIDENTE'|None}` según los grupos Django del usuario autenticado (superuser → ADMIN, grupo ADMIN → ADMIN, grupo ORGANIZADOR → ORGANIZADOR, resto → RESIDENTE).
  - Registrar `'website.context_processors.user_rol'` en la lista `context_processors` de `TEMPLATES` en `dcrm/settings.py`.
  - _Requisitos: Requirement 1 (AC1), Requirement 5 (AC2, AC3)_

- [x] 2. Implementar OrgAdminRequiredMixin
  - Agregar la clase `OrgAdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin)` en `website/views.py`. El método `test_func` retorna `True` si el usuario es superuser o pertenece a grupos `ADMIN` u `ORGANIZADOR`.
  - El método `handle_no_permission` devuelve JSON 403 con mensaje de acceso denegado para peticiones AJAX, y redirige a `home` con `messages.error` para peticiones normales.
  - Reemplazar `AdminRequiredMixin` por `OrgAdminRequiredMixin` en `JornadaListView`, `JornadaCreateView`, `JornadaUpdateView` y `JornadaDeleteView`.
  - _Requisitos: Requirement 1 (AC1), Requirement 3 (AC1, AC2)_

- [x] 3. Agregar validaciones al modelo Jornada y al formulario JornadaForm
  - En el método `clean()` de `Jornada`, agregar validación de unicidad barrio+fecha+hora: si existe otra jornada con el mismo `barrio` (case-insensitive), misma `fecha` y `estado` en `['pendiente', 'activa']`, lanzar `ValidationError` excluyendo el propio objeto con `.exclude(pk=self.pk)`.
  - En `JornadaForm.clean_descripcion()`, agregar rechazo de descripciones con más de 500 caracteres además del mínimo de 10 ya existente.
  - _Requisitos: Requirement 2 (AC1, AC3, AC5), Requirement 1 (AC7)_

- [x] 4. Actualizar JornadaUpdateView con guardia de estado y validación de organizador
  - Agregar el método `get_object()` que lanza `PermissionDenied` si `jornada.estado != 'pendiente'`. Para peticiones AJAX, capturar en `dispatch()` y devolver JSON 403 con mensaje "Solo se pueden editar o cancelar jornadas en estado pendiente."
  - En `form_valid()`, si el formulario intenta cambiar `estado` a `activa` y `id_organizador` es `None`, añadir error de formulario y devolver `form_invalid()` con mensaje "La jornada debe tener al menos un organizador antes de publicarse."
  - _Requisitos: Requirement 3 (AC1, AC3, AC6)_

- [x] 5. Refactorizar JornadaDeleteView para cancelación lógica con alerta de cupo
  - Cambiar el método `post()` para que en lugar de eliminar el registro, realice cancelación lógica: `jornada.estado = 'cancelada'` + `jornada.save()`. Responder con JSON `{success: true, message: 'Jornada cancelada exitosamente.', toast_category: 'success'}`.
  - Agregar guardia de estado en `get_object()` que lanza `PermissionDenied` si `estado != 'pendiente'`.
  - En el método `get()` (GET AJAX para mostrar el partial de confirmación), calcular si los inscritos superan el 50% del cupo máximo y pasar `advertencia_cupo=True` al contexto del template.
  - _Requisitos: Requirement 3 (AC2, AC3, AC4, AC5)_

- [x] 6. Crear JornadaDisponiblesView
  - Crear `JornadaDisponiblesView(LoginRequiredMixin, ListView)` en `views.py` con `template_name='jornada_disponibles.html'` y `context_object_name='jornadas'`.
  - En `get_queryset()`: filtrar `estado='activa'` y `fecha__gte=timezone.now()`, ordenar por `fecha` ascendente. Si el usuario no es ADMIN/ORGANIZADOR/superuser, filtrar además por `barrio__iexact=user.registro.barrio`; si no tiene `Registro`, devolver `Jornada.objects.none()`.
  - En `get_context_data()`, pasar `inscripciones_ids` (set de `jornada_id` de las inscripciones del usuario autenticado) al template para controlar el estado del botón de inscripción.
  - _Requisitos: Requirement 5 (AC1, AC2, AC3, AC4, AC5, AC6, AC7)_

- [x] 7. Crear vista inscribir_jornada
  - Crear la función `inscribir_jornada(request, pk)` decorada con `@login_required` en `views.py`. Solo acepta POST; devolver JSON 405 para GET.
  - Verificar que la jornada existe y `estado == 'activa'`; si no, devolver JSON `{success: false, toast_category: 'danger'}`.
  - Verificar que el usuario no tiene ya una `Inscripcion` para esa jornada; si existe, devolver JSON `{success: false, message: 'Ya estás inscrito en esta jornada.', toast_category: 'warning'}`.
  - Verificar que `inscripciones.count() < cupo_maximo`; si el cupo está lleno, devolver JSON `{success: false, message: 'Esta jornada no tiene cupo disponible.', toast_category: 'danger'}`.
  - Crear la `Inscripcion` y devolver JSON `{success: true, message: '¡Inscripción realizada exitosamente!', toast_category: 'success'}`.
  - _Requisitos: Requirement 5 (AC7)_

- [x] 8. Crear MisInscripcionesView y AsistenciaRegistrarView
  - Crear `MisInscripcionesView(LoginRequiredMixin, ListView)` con `template_name='mis_inscripciones.html'`. En `get_queryset()` retornar `Inscripcion.objects.filter(residente=self.request.user).select_related('jornada').order_by('-fecha_inscripcion')`.
  - Crear `AsistenciaRegistrarView(OrgAdminRequiredMixin, View)`. El método `get()` renderiza `asistencia.html` con las inscripciones de la jornada indicada por parámetro GET `jornada_id`. El método `post()` hace `Inscripcion.objects.filter(pk__in=ids).update(asistencia=True, confirmada=True)` y devuelve JSON `{success: true, message: 'Asistencia registrada.', toast_category: 'success'}`.
  - _Requisitos: Requirement 5 (AC1), Requirement 3 (AC5)_

- [x] 9. Crear ReportesView
  - Crear `ReportesView(OrgAdminRequiredMixin, TemplateView)` con `template_name='reportes.html'`.
  - En `get_context_data()` incluir: conteo de jornadas agrupadas por estado, top 5 jornadas con más inscritos, y porcentaje de asistencia promedio usando anotaciones del ORM.
  - _Requisitos: Requirement 5 (AC3)_

- [x] 10. Registrar todas las URLs nuevas en website/urls.py
  - Agregar rutas: `jornadas/disponibles/` → `jornada_disponibles`, `jornadas/<int:pk>/inscribir/` → `jornada_inscribir`, `mis-inscripciones/` → `mis_inscripciones`, `asistencia/` → `asistencia_registrar`, `reportes/` → `reportes`.
  - Asegurarse de que `jornadas/disponibles/` está definida **antes** de `jornadas/<int:pk>/` para evitar conflictos de captura de URL.
  - _Requisitos: todos_

- [x] 11. Actualizar navbar.html con menú por rol
  - Reemplazar el contenido estático del navbar por lógica condicional basada en `user_rol`: si `ADMIN` u `ORGANIZADOR` → mostrar "Dashboard", "Crear Jornada" (`.load-spa`), "Registrar Asistencia" y "Reportes"; si `RESIDENTE` → mostrar "Jornadas Disponibles" y "Mis Inscripciones".
  - Eliminar los ítems hardcoded que ya no aplican ("Servicios", "Productos", "Agendas", "Mas opciones") o mostrarlos solo cuando el usuario no está autenticado.
  - Verificar que ningún ítem del navbar hace referencia a CDN externo.
  - _Requisitos: Requirement 1 (AC1), Requirement 5 (AC2, AC3)_

- [x] 12. Corregir partials/jornada_list.html con campos del modelo real
  - Reemplazar los campos del modelo antiguo (`jornada.nombre`, `jornada.activo`, `jornada.hora_inicio`, etc.) por los campos reales: `jornada.titulo`, `jornada.barrio`, `jornada.fecha`, `jornada.direccion`, `jornada.tipo_material`, `jornada.cupo_maximo`, `jornada.estado`.
  - Agregar badge de estado con colores Bootstrap: `pendiente` → `bg-warning text-dark`, `activa` → `bg-success`, `cancelada` → `bg-danger`, `finalizada` → `bg-secondary`.
  - Agregar indicador de cupo usando `{% with inscritos=jornada.inscripciones.count %}`: si `inscritos >= cupo_maximo` mostrar badge "Cupo agotado" (`bg-danger`); si no, mostrar `inscritos/cupo_maximo inscritos`.
  - _Requisitos: Requirement 5 (AC6, AC7)_

- [x] 13. Corregir partials/jornada_form.html con campos del modelo real
  - Reemplazar los campos del modelo de turnos por los campos reales de `JornadaForm`: `titulo`, `descripcion`, `fecha`, `direccion`, `barrio`, `tipo_material`, `cupo_maximo`, `estado`, `id_organizador`.
  - Agregar `<label for="{{ form.<campo>.id_for_label }}">` y bloque de errores inline `{% if form.<campo>.errors %}<div class="invalid-feedback d-block">{% endif %}` para cada campo.
  - Asegurarse de que el `<form>` tiene clase `ajax-form` y atributo `action` correcto según contexto (crear o editar).
  - _Requisitos: Requirement 1 (AC2, AC4, AC5), Requirement 2 (AC3, AC4)_

- [x] 14. Actualizar partials/jornada_confirm_delete.html con alerta de cupo
  - Mostrar un `Alert` Bootstrap `alert-warning` cuando `advertencia_cupo` sea `True` en el contexto, advirtiendo que más del 50% del cupo ya está inscrito.
  - El formulario de confirmación debe tener clase `ajax-delete-form` y hacer POST a `{% url 'jornada_delete' object.pk %}`.
  - Incluir botón "Cancelar operación" (`.load-spa` que vuelve al listado) y botón "Confirmar cancelación" (submit).
  - _Requisitos: Requirement 3 (AC4)_

- [x] 15. Crear partials/jornada_card_residente.html
  - Crear el archivo con una tarjeta Bootstrap que muestre: `titulo`, badge de `tipo_material`, `fecha` formateada (`d/m/Y H:i`), `barrio`, `direccion` y `descripcion`.
  - En el footer, mostrar con lógica condicional: botón deshabilitado "Cupo agotado" si `inscritos >= cupo_maximo`; botón deshabilitado "✓ Ya inscrito" si `jornada.pk in inscripciones_ids`; botón `.inscribir-btn` con `data-url="{% url 'jornada_inscribir' jornada.pk %}"` en caso contrario.
  - _Requisitos: Requirement 5 (AC6, AC7)_

- [x] 16. Crear template jornada_disponibles.html
  - Crear `jornada_disponibles.html` extendiendo `base.html`. Mostrar jornadas como grid de tarjetas usando `{% include 'partials/jornada_card_residente.html' %}` dentro de un `{% for %}`.
  - Mostrar estado vacío diferenciado según `user_rol`: RESIDENTE → "No hay jornadas activas disponibles en tu barrio"; ADMIN/ORGANIZADOR → "No hay jornadas activas disponibles".
  - Incluir `<script src="{% static 'js/spa_motor.js' %}"></script>` al final del bloque `content`.
  - _Requisitos: Requirement 5 (AC1, AC2, AC3, AC4, AC5)_

- [x] 17. Crear templates mis_inscripciones.html, asistencia.html y reportes.html
  - `mis_inscripciones.html`: tabla Bootstrap con columnas `Jornada`, `Fecha`, `Barrio`, `Estado inscripción`, `Asistencia confirmada`. Estado vacío: "No tienes inscripciones registradas."
  - `asistencia.html`: formulario con clase `ajax-form` que lista inscripciones de una jornada con checkbox por inscripción para marcar asistencia. Toast de éxito al guardar.
  - `reportes.html`: cards con métricas (total jornadas por estado, top 5 jornadas con más inscritos, % asistencia promedio). Accesible solo para ADMIN/ORGANIZADOR.
  - _Requisitos: Requirement 5 (AC3)_

- [x] 18. Actualizar jornada_home.html con #spa-panel
  - Agregar `<div id="spa-panel">` dentro de `#spa-content` como zona de inyección de partials. El botón "Nueva Jornada" debe tener `data-target="#spa-panel"`.
  - El `{% include 'partials/jornada_list.html' %}` inicial debe estar dentro de `#spa-panel`.
  - _Requisitos: Requirement 1 (AC6)_

- [x] 19. Extender spa_motor.js con handler de inscripción
  - Dentro del IIFE existente, agregar listener `click` para `.inscribir-btn` que haga `fetch` POST a `btn.dataset.url` con headers `X-Requested-With` y `X-CSRFToken`.
  - En el `.then()`: llamar a `showToast(data.message, data.toast_category)`. Si `data.success`, deshabilitar el botón, cambiar texto a "✓ Ya inscrito" y clase a `btn-outline-success`.
  - En el `.catch()`: llamar a `showToast('Error de conexión.', 'danger')`.
  - _Requisitos: Requirement 5 (AC7)_

- [x] 20. Verificación final e integración
  - Ejecutar `python manage.py check` en el directorio `inventario_django/dcrm` y resolver cualquier error de configuración.
  - Verificar que todas las URLs resuelven sin conflictos ejecutando `python manage.py show_urls` o comprobando manualmente cada ruta.
  - Confirmar que ningún template tiene referencias a CDN externo buscando `cdn.jsdelivr`, `cdnjs` o `unpkg` en todos los archivos `.html`.
  - _Requisitos: todos_

## Task Dependency Graph

```json
{
  "waves": [
    { "wave": 1, "tasks": [1, 2, 3] },
    { "wave": 2, "tasks": [4, 5, 6, 7, 8, 9] },
    { "wave": 3, "tasks": [10, 11, 12, 13, 14, 15] },
    { "wave": 4, "tasks": [16, 17, 18, 19] },
    { "wave": 5, "tasks": [20] }
  ],
  "dependencies": {
    "4":  ["2", "3"],
    "5":  ["2"],
    "6":  ["1"],
    "7":  ["2"],
    "8":  ["2"],
    "9":  ["2"],
    "10": ["4", "5", "6", "7", "8", "9"],
    "11": ["1"],
    "12": ["2"],
    "13": ["3"],
    "14": ["5"],
    "15": ["6", "7"],
    "16": ["6", "15"],
    "17": ["8", "9"],
    "18": ["12"],
    "19": ["7"],
    "20": ["10", "11", "12", "13", "14", "15", "16", "17", "18", "19"]
  }
}
```

## Notes

- Los modelos `Jornada`, `Registro` e `Inscripcion` ya existen en `models.py`. La tarea 3 solo agrega validaciones, no requiere migraciones nuevas.
- Los archivos estáticos de Bootstrap (`bootstrap.min.css`, `bootstrap.bundle.min.js`) ya están en `website/templates/static/`. No modificar `STATICFILES_DIRS`.
- El `toast-container` ya existe en `base.html` y `showToast()` en `spa_motor.js`. Las tareas de templates solo deben garantizar que las respuestas JSON incluyan `toast_category`.
- La fuente Google Fonts en `base.html` puede dejarse si ya estaba o eliminarse para entorno completamente offline; no es un CDN de Bootstrap.
- Las tareas 1–10 son de backend puro y pueden implementarse y probarse antes de tocar los templates (tareas 11–19).
