from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

sql_injection_pattern = r'(;|\-\-|OR|AND|UNION|SELECT|INSERT|DELETE|UPDATE|DROP|EXEC|EXECUTE|xp_|sp_|0x)'


def validate_no_sql_injection(value):
    """Validador personalizado para prevenir inyecciones SQL"""
    import re
    if re.search(sql_injection_pattern, value, re.IGNORECASE):
        raise ValidationError('Caracteres sospechosos no permitidos.')


class Jornada(models.Model):
    """Modelo para gestión de turnos/horarios laborales"""
    
    nombre = models.CharField(
        max_length=100,
        validators=[RegexValidator(
            regex=rf'^(?!.*(?:;|\-\-|OR|AND|UNION|SELECT|INSERT|DELETE|UPDATE|DROP|EXEC|EXECUTE|xp_|sp_|0x)).*$',
            message='Caracteres sospechosos no permitidos.',
            code='sql_injection_blocked'
        )],
        help_text='Nombre del turno (ej: Mañana, Tarde, Noche)'
    )
    
    hora_inicio = models.TimeField(help_text='Hora de inicio del turno')
    hora_fin = models.TimeField(help_text='Hora de fin del turno')
    
    dias_trabajo = models.CharField(
        max_length=50,
        validators=[RegexValidator(
            regex=rf'^(?!.*(?:;|\-\-|OR|AND|UNION|SELECT|INSERT|DELETE|UPDATE|DROP|EXEC|EXECUTE|xp_|sp_|0x)).*$',
            message='Caracteres sospechosos no permitidos.',
            code='sql_injection_blocked'
        )],
        help_text='Días de trabajo (ej: L-M-M-V-F)'
    )
    
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Jornada'
        verbose_name_plural = 'Jornadas'
        ordering = ['hora_inicio']

    def __str__(self):
        from django.utils import timezone
        return f"{self.nombre} ({self.hora_inicio.strftime('%H:%M')} - {self.hora_fin.strftime('%H:%M')})"


class Registro(models.Model):
    """Modelo para el registro de usuarios en el sistema CRM"""
    
    # Campos relacionados con el usuario de Django
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='registro')
    
    # Campos adicionales de información personal
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    
    # Campos de fecha
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Registro'
        verbose_name_plural = 'Registros'
        ordering = ['-fecha_registro']
    
    def __str__(self):
        return f"{self.user.username} - {self.ciudad or 'Sin ciudad'}"
