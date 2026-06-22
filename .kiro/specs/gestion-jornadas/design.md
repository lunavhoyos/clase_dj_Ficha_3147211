# Design Document — Gestión de Jornadas de Recolección

## Overview

Este documento describe el diseño técnico para implementar el módulo de **Gestión de Jornadas de Recolección** sobre el proyecto Django existente (`dcrm`, app `website`).

La arquitectura sigue el patrón **SPA liviana sobre Django**: el servidor renderiza fragmentos HTML via AJAX y los inyecta en el DOM sin recargar la página. El motor SPA (`spa_motor.js`) ya existe y se reutiliza. Todo el estilo usa **Bootstrap local** cargado con `{% load static %}`, sin CDN.

Restricciones de diseño:

| Restricción | Decisión |
|---|---|
| Bootstrap | Solo archivos locales: `{% static "css/bootstrap.min.css" %}` y `{% static "js/bootstrap.bundle.min.js" %}` |
| Notificaciones | Toasts Bootstrap via `spa_motor.js` + `toast_alert.html` |
| Roles | Grupos Django: `ADMIN`, `ORGANIZADOR`, `RESIDENTE` |
| SPA | Motor AJAX `spa_motor.js` existente con clases `.load-spa` y `.ajax-form` |
| Modelos existentes | `Jornada`, `Registro`, `Inscripcion` ya definidos en `models.py` |

---

## Architecture

El módulo sigue una arquitectura de **tres capas** sobre Django MVT:

```
┌─────────────────────────────────────────────────┐
│  Capa de Presentación (Templates + spa_motor.js) │
│  base.html → navbar.html (menú por rol)          │
│  #spa-content → #spa-panel (zona intercambiable) │
└────────────────────┬────────────────────────────┘
                     │ AJAX (fetch + JSON)
┌────────────────────▼────────────────────────────┐
│  Capa de Vistas (views.py)                       │
│  OrgAdminRequiredMixin + vistas CRUD + REST-like │
│  context_processors.py (user_rol)                │
└────────────────────┬────────────────────────────┘
                     │ ORM
┌────────────────────▼────────────────────────────┐
│  Capa de Datos (models.py)                       │
│  Jornada · Inscripcion · Registro                │
└─────────────────────────────────────────────────┘
```

### Menú SPA por rol

```
ADMIN / ORGANIZADOR              RESIDENTE
─────────────────────────        ──────────────────────
• Dashboard                      • Jornadas Disponibles
• Crear Jornada                  • Mis Inscripciones
• Registrar Asistencia
• Reportes
```

El navbar se controla con la variable de contexto `user_rol` inyectada desde un **context processor** (`website/context_processors.py`) registrado en `settings.py`.

### Flujo de datos — Crear jornada (ADMIN/ORGANIZADOR)

```
Clic "Crear Jornada" (.load-spa)
  → GET /jornadas/crear/ [AJAX X-Requested-With]
    → JornadaCreateView → render partials/jornada_form.html
  → spa_motor.js inyecta HTML en #spa-panel

Submit formulario (.ajax-form)
  → POST /jornadas/crear/ [AJAX]
    → JornadaForm.is_valid() → Jornada.clean() → save()
    → JSON { success, message, toast_category }
  → spa_motor.js → showToast() + recarga jornada_list
```

### Flujo de datos — Inscribirse (RESIDENTE)

```
Clic "Inscribirse" (.inscribir-btn)
  → POST /jornadas/<pk>/inscribir/ [AJAX]
    → valida cupo y duplicado → Inscripcion.create()
    → JSON { success, message, toast_category }
  → showToast() + botón deshabilitado visualmente
```

### Flujo de datos — Cancelar con confirmación

```
Clic "Cancelar" (.load-spa)
  → GET /jornadas/<pk>/eliminar/ [AJAX]
    → render jornada_confirm_delete.html
    → si inscritos > 50% cupo → Bootstrap Alert de advertencia

Confirmar en partial
  → POST /jornadas/<pk>/eliminar/ [AJAX]
    → jornada.estado = 'cancelada' → save()
    → JSON { success, message, toast_category: 'success' }
  → showToast() + card eliminada del DOM
```

---

## Components and Interfaces

### `website/context_processors.py` (nuevo)

```python
def user_rol(request):
    """Inyecta el rol del usuario en todos los templates."""
    if not request.user.is_authenticated:
        return {'user_rol': None}
    u = request.user
    if u.is_superuser or u.groups.filter(name='ADMIN').exists():
        return {'user_rol': 'ADMIN'}
    if u.groups.filter(name='ORGANIZADOR').exists():
        return {'user_rol': 'ORGANIZADOR'}
    return {'user_rol': 'RESIDENTE'}
```

Registrar en `settings.py`:
```python
'website.context_processors.user_rol',
```

### `OrgAdminRequiredMixin` (views.py)

Reemplaza `AdminRequiredMixin` en vistas de jornadas para incluir al `ORGANIZADOR`:

```python
class OrgAdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        u = self.request.user
        return u.is_superuser or u.groups.filter(name__in=['ADMIN', 'ORGANIZADOR']).exists()

    def handle_no_permission(self):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Acceso denegado.'}, status=403)
        messages.error(self.request, 'No tienes permisos suficientes para acceder a esta sección.')
        return redirect('home')
```

### Vistas existentes (modificar)

| Vista | Cambio |
|---|---|
| `JornadaListView` | Usar `OrgAdminRequiredMixin` |
| `JornadaCreateView` | Usar `OrgAdminRequiredMixin`; respuesta JSON con `toast_category` |
| `JornadaUpdateView` | Usar `OrgAdminRequiredMixin`; guardia de estado `pendiente` en `get_object` |
| `JornadaDeleteView` | Cambiar a cancelación lógica (`estado='cancelada'`); guardia 50% cupo |

### Vistas nuevas

| Vista | URL name | Clase/función | Descripción |
|---|---|---|---|
| `JornadaDisponiblesView` | `jornada_disponibles` | `LoginRequiredMixin + ListView` | Filtra por rol y barrio |
| `inscribir_jornada` | `jornada_inscribir` | función `@login_required` | POST; crea `Inscripcion`; devuelve JSON |
| `MisInscripcionesView` | `mis_inscripciones` | `LoginRequiredMixin + ListView` | Inscripciones del usuario autenticado |
| `AsistenciaRegistrarView` | `asistencia_registrar` | `OrgAdminRequiredMixin + View` | Marca `asistencia=True` en inscripción |
| `ReportesView` | `reportes` | `OrgAdminRequiredMixin + TemplateView` | Resumen estadístico |

### URLs (`website/urls.py`)

```python
# Gestión (ADMIN/ORGANIZADOR)
path('jornadas/', JornadaListView.as_view(), name='jornada_list'),
path('jornadas/crear/', JornadaCreateView.as_view(), name='jornada_create'),
path('jornadas/<int:pk>/editar/', JornadaUpdateView.as_view(), name='jornada_update'),
path('jornadas/<int:pk>/eliminar/', JornadaDeleteView.as_view(), name='jornada_delete'),

# Residente
path('jornadas/disponibles/', JornadaDisponiblesView.as_view(), name='jornada_disponibles'),
path('jornadas/<int:pk>/inscribir/', inscribir_jornada, name='jornada_inscribir'),
path('mis-inscripciones/', MisInscripcionesView.as_view(), name='mis_inscripciones'),

# Asistencia y reportes
path('asistencia/', AsistenciaRegistrarView.as_view(), name='asistencia_registrar'),
path('reportes/', ReportesView.as_view(), name='reportes'),
```

### Templates

```
website/templates/
├── base.html                        (sin CDN — ya cumple)
├── navbar.html                      (modificar: menú por user_rol)
├── jornada_home.html                (modificar: #spa-panel)
├── jornada_disponibles.html         (nuevo)
├── mis_inscripciones.html           (nuevo)
├── asistencia.html                  (nuevo)
├── reportes.html                    (nuevo)
└── partials/
    ├── jornada_list.html            (modificar: campos reales del modelo)
    ├── jornada_form.html            (modificar: campos reales del modelo)
    ├── jornada_confirm_delete.html  (modificar: alerta 50% cupo)
    ├── jornada_card_residente.html  (nuevo)
    └── toast_alert.html             (sin cambios)
```

### `spa_motor.js` — extensión para inscripción

Añadir handler `.inscribir-btn` al módulo IIFE existente:

```javascript
document.addEventListener('click', function(e) {
    const btn = e.target.closest('.inscribir-btn');
    if (!btn) return;
    e.preventDefault();
    fetch(btn.dataset.url, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': getCookie('csrftoken') }
    })
    .then(r => r.json())
    .then(data => {
        showToast(data.message, data.toast_category || (data.success ? 'success' : 'danger'));
        if (data.success) {
            btn.disabled = true;
            btn.textContent = '✓ Ya inscrito';
            btn.classList.replace('btn-primary', 'btn-outline-success');
        }
    })
    .catch(() => showToast('Error de conexión.', 'danger'));
});
```

---

## Data Models

### `Jornada` (ya existe — agregar validación en `clean()`)

```
Jornada
├── id (PK, AutoField)
├── titulo          CharField(200)
├── descripcion     TextField  [min 10, max 500]
├── fecha           DateTimeField  [debe ser futura]
├── direccion       CharField(255)
├── barrio          CharField(100)
├── tipo_material   CharField(20, choices)
├── cupo_maximo     IntegerField  [1–200]
├── estado          CharField(20, choices)  [pendiente|activa|finalizada|cancelada]
├── id_organizador  ForeignKey(User, null=True)
├── fecha_creacion  DateTimeField(auto_now_add)
└── fecha_actualizacion DateTimeField(auto_now)
```

Validación adicional en `clean()` (unicidad barrio+fecha+hora):
```python
if self.fecha and self.barrio:
    conflicto = Jornada.objects.filter(
        barrio__iexact=self.barrio,
        fecha=self.fecha,
        estado__in=['pendiente', 'activa']
    ).exclude(pk=self.pk)
    if conflicto.exists():
        raise ValidationError('Ya existe una jornada activa en este barrio para esa fecha y hora.')
```

### `Inscripcion` (ya existe — sin cambios)

```
Inscripcion
├── id (PK)
├── residente   ForeignKey(User)
├── jornada     ForeignKey(Jornada)
├── fecha_inscripcion DateTimeField(auto_now_add)
├── asistencia  BooleanField(default=False)
└── confirmada  BooleanField(default=False)
UniqueConstraint: (residente, jornada)
```

### `Registro` (ya existe — sin cambios)

```
Registro
├── id (PK)
├── user    OneToOneField(User)
├── barrio  CharField(100)   ← usado para filtrar jornadas por barrio
└── ...
```

### `JornadaForm` (ya existe — agregar validación de descripción max 500 chars)

```python
def clean_descripcion(self):
    desc = self.cleaned_data.get('descripcion', '')
    if len(desc.strip()) < 10:
        raise forms.ValidationError('La descripción debe tener al menos 10 caracteres.')
    if len(desc.strip()) > 500:
        raise forms.ValidationError('La descripción no puede superar los 500 caracteres.')
    return desc
```

---

## Error Handling

| Escenario | Comportamiento |
|---|---|
| Usuario sin rol accede a ruta protegida | `OrgAdminRequiredMixin.handle_no_permission()` → JSON 403 (AJAX) o redirect con `messages.error` |
| Formulario con campos inválidos | `form_invalid()` → JSON con HTML del formulario con errores inline |
| Editar/cancelar jornada no-pendiente | `get_object()` lanza `PermissionDenied` → JSON 403 con mensaje |
| Inscripción duplicada | `inscribir_jornada()` → JSON `{success: false, toast_category: 'warning'}` |
| Cupo agotado | `inscribir_jornada()` → JSON `{success: false, toast_category: 'danger'}` |
| Error de red en fetch | `spa_motor.js` `.catch()` → `showToast('Error de conexión.', 'danger')` |
| Jornada sin organizador al publicar | `JornadaUpdateView.form_valid()` verifica `id_organizador` antes de cambiar estado a `activa` |

---

## Correctness Properties

### Property 1: Estado activa requiere organizador
Una `Jornada` nunca puede tener `estado='activa'` sin `id_organizador` asignado. Validado en `form_valid()` de `JornadaUpdateView` antes de persistir el cambio de estado.
**Validates: Requirement 3.6**

### Property 2: Unicidad de inscripción
Una `Inscripcion` es única por `(residente, jornada)`. Garantizado por `unique_together` en el modelo y verificación previa en `inscribir_jornada()`.
**Validates: Requirement 5.7**

### Property 3: Rango de cupo máximo
`Jornada.cupo_maximo` siempre está entre 1 y 200. Validado en `JornadaForm.clean_cupo_maximo()` y en `Jornada.clean()`.
**Validates: Requirement 2.2, Requirement 2.4**

### Property 4: Fecha futura obligatoria
`Jornada.fecha` siempre es posterior al momento de creación. Validado en `JornadaForm.clean_fecha()`.
**Validates: Requirement 1.3, Requirement 1.5**

### Property 5: Cupo no superable
El número de inscritos activos nunca supera `cupo_maximo`. Verificado en `inscribir_jornada()` antes de crear la inscripción.
**Validates: Requirement 2.2, Requirement 5.7**

### Property 6: Edición solo en estado pendiente
Solo jornadas con `estado='pendiente'` pueden editarse o cancelarse. Guardia implementada en `get_object()` de `JornadaUpdateView` y `JornadaDeleteView`.
**Validates: Requirement 3.1, Requirement 3.2, Requirement 3.3**

---

## Testing Strategy

- **Unitario (Django TestCase)**: validaciones de `Jornada.clean()`, `JornadaForm`, y lógica de `inscribir_jornada()`.
- **Integración (Django Client)**: flujo completo de creación, edición, cancelación e inscripción via peticiones AJAX simuladas con cabecera `X-Requested-With`.
- **Control de acceso**: verificar que rutas protegidas devuelven 403 para usuarios sin rol correcto.
- **Verificación manual**: toasts visibles tras cada acción; menú correcto según rol; filtro por barrio activo para residentes.
