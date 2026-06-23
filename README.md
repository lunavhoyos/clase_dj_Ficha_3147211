# Clase DJ - Ficha 3147211

Proyecto educativo desarrollado con Django, Bootstrap y tecnologías web modernas.

## 📋 Descripción

Este proyecto es una aplicación web construida con **Django** como framework backend, **Bootstrap** para el diseño responsivo, y tecnologías web estándar (HTML, CSS, JavaScript) para el frontend. [...]

## 🛠️ Tecnologías Utilizadas

| Tecnología | Porcentaje | Descripción |
|-----------|-----------|-------------|
| HTML | 55.7% | Estructura y marcado de la aplicación |
| Python | 30.7% | Lógica backend con Django |
| CSS | 9.4% | Estilos y diseño responsivo |
| JavaScript | 4.2% | Interactividad del lado del cliente |

### Stack Principal

- **Backend**: Python + Django
- **Frontend**: HTML5, CSS3, Bootstrap
- **Base de datos**: SQLite (por defecto en Django)
- **Gestor de dependencias**: pip

## 🚀 Instalación y Configuración

### Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Entorno virtual (recomendado)

### Pasos de Instalación

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/lunavhoyos/clase_dj_Ficha_3147211.git
   cd clase_dj_Ficha_3147211
   ```

2. **Crear un entorno virtual**
   ```bash
   python -m venv venv
   ```

3. **Activar el entorno virtual**
   - En Windows:
     ```bash
     venv\Scripts\activate
     ```
   - En macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

5. **Realizar migraciones**
   ```bash
   python manage.py migrate
   ```

6. **Crear un superusuario (opcional)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Ejecutar el servidor de desarrollo**
   ```bash
   python manage.py runserver
   ```

   La aplicación estará disponible en: `http://localhost:8000`

## 📁 Estructura del Proyecto

```
clase_dj_Ficha_3147211/
│
├── manage.py                 # Script de gestión de Django
├── requirements.txt          # Dependencias del proyecto
├── README.md                 # Este archivo
│
├── [nombre_del_app]/         # Aplicación Django principal
│   ├── migrations/           # Migraciones de base de datos
│   ├── static/               # Archivos estáticos (CSS, JS, imágenes)
│   ├── templates/            # Plantillas HTML
│   ├── models.py             # Modelos de datos
│   ├── views.py              # Vistas y lógica
│   ├── urls.py               # Rutas de la aplicación
│   └── admin.py              # Configuración del panel admin
│
└── [nombre_del_proyecto]/    # Configuración principal del proyecto
    ├── settings.py           # Configuración de Django
    ├── urls.py               # Rutas principales
    └── wsgi.py               # Configuración WSGI
```

## 📖 Uso

1. **Acceder a la aplicación**: Abre tu navegador en `http://localhost:8000`
2. **Panel de administración**: Accede a `http://localhost:8000/admin` con las credenciales del superusuario
3. **Navegar por las funcionalidades**: Utiliza la interfaz para explorar las características de la aplicación

## 🎓 Propósito Educativo

Este proyecto está diseñado para enseñar y practicar:

- ✅ Conceptos fundamentales de Django
- ✅ Creación de modelos y migraciones
- ✅ Desarrollo de vistas y templates
- ✅ Integración de Bootstrap para diseño responsivo
- ✅ Uso de formularios Django
- ✅ Autenticación y autorización básica
- ✅ Buenas prácticas en desarrollo web

## 🧩 Patrones de diseño

El proyecto aplica varios patrones de diseño y buenas prácticas que ayudan a la organización y mantenibilidad del código. A continuación un resumen con referencias a los archivos donde se aplican:

- Arquitectura Modelo–Plantilla–Vista (MTV): organización estándar de Django (ver `inventario_django/dcrm/dcrm/settings.py` y la app `website`).
- Active Record: los modelos de Django implementan entidades y lógica asociada (ver `inventario_django/dcrm/website/models.py`: clases `Jornada`, `Registro`, `Inscripcion`).
- Class-based Views / Template Method: uso de vistas basadas en clases que extienden y sobreescriben métodos (ver `inventario_django/dcrm/website/views.py`: `JornadaListView`, `JornadaCreateView`, `JornadaUpdateView`).
- Mixin pattern (composición de comportamiento): `OrgAdminRequiredMixin` y uso de `LoginRequiredMixin`/`UserPassesTestMixin` para control de acceso (`inventario_django/dcrm/website/views.py`).
- Decorator pattern: decoradores como `@login_required` y `@method_decorator(ensure_csrf_cookie, name='dispatch')` para añadir comportamiento transversal.
- Observer pattern (señales): archivo `inventario_django/dcrm/website/signals.py` preparado para señales (`post_save`, etc.).
- Validator / Strategy: validadores personalizados para prevenir inyección SQL y encapsular reglas (ver `inventario_django/dcrm/website/models.py`).
- Domain Model: reglas de negocio encapsuladas dentro de los modelos (`clean()`, propiedades como `cupo_disponible`, `porcentaje_inscripcion`).
- Facade / Adaptador (implícito): vistas que unifican respuestas HTML y JSON para peticiones normales y AJAX (uso de `render_to_string` + `JsonResponse` en `views.py`).

Evidencia (fragmentos relevantes):
- `inventario_django/dcrm/website/models.py` — validadores y modelos con lógica: validator y clases `Jornada`, `Registro`, `Inscripcion`.
- `inventario_django/dcrm/website/views.py` — mixins, CBV, manejo AJAX y control de acceso.
- `inventario_django/dcrm/website/signals.py` — archivo de señales.
- `inventario_django/dcrm/website/urls.py` — rutas y mapeo de vistas.
- `inventario_django/dcrm/dcrm/settings.py` — configuración y apps instaladas.

Si quieres que incluya ejemplos de código con números de línea directamente en el README o que amplíe la explicación para cada patrón, dime y lo agrego.

## 📝 Notas Importantes

- Esta es una aplicación educativa. Para producción, requiere configuraciones de seguridad adicionales
- Asegúrate de cambiar la `SECRET_KEY` en `settings.py` antes de desplegar
- Configura las variables de entorno apropiadamente (DEBUG, ALLOWED_HOSTS, etc.)

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está disponible bajo la licencia MIT. Ver el archivo LICENSE para más detalles.

## 📧 Contacto

**Autor**: Luna Vhoyos

Para preguntas o sugerencias, puedes abrir un issue en el repositorio.

---

**Última actualización**: Junio 2026
