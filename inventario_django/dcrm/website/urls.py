from django.urls import path
from . import views

urlpatterns = [
    # Autenticación y home
    path('', views.home, name='home'),
    path('registro/', views.registro_view, name='registro'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Registros de usuarios
    path('edit_record/<int:record_id>/', views.edit_record, name='edit_record'),
    path('delete_record/<int:record_id>/', views.delete_record, name='delete_record'),
    path('add_record/', views.add_record, name='add_record'),

    # Jornadas — Gestión (ADMIN / ORGANIZADOR)
    # IMPORTANTE: rutas literales ANTES de rutas con <int:pk>
    path('jornadas/', views.JornadaListView.as_view(), name='jornada_list'),
    path('jornadas/home/', views.JornadaListView.as_view(), name='jornada_home'),
    path('jornadas/crear/', views.JornadaCreateView.as_view(), name='jornada_create'),
    path('jornadas/disponibles/', views.JornadaDisponiblesView.as_view(), name='jornada_disponibles'),
    path('jornadas/<int:pk>/editar/', views.JornadaUpdateView.as_view(), name='jornada_update'),
    path('jornadas/<int:pk>/eliminar/', views.JornadaDeleteView.as_view(), name='jornada_delete'),
    path('jornadas/<int:pk>/inscribir/', views.inscribir_jornada, name='jornada_inscribir'),

    # Residente
    path('mis-inscripciones/', views.MisInscripcionesView.as_view(), name='mis_inscripciones'),

    # Asistencia y reportes (ADMIN / ORGANIZADOR)
    path('asistencia/', views.AsistenciaRegistrarView.as_view(), name='asistencia_registrar'),
    path('reportes/', views.ReportesView.as_view(), name='reportes'),
]
