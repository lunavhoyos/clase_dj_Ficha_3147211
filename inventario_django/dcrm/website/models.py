from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator, MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone

sql_injection_pattern = r'(;|\-\-|OR|AND|UNION|SELECT|INSERT|DELETE|UPDATE|DROP|EXEC|EXECUTE|xp_|sp_|0x)'


def validate_no_sql_injection(value):
    """Validador personalizado para prevenir inyecciones SQL"""
    import re
    if re.search(sql_injection_pattern, value, re.IGNORECASE):
        raise ValidationError('Caracteres sospechosos no permitidos.')


class Jornada(models.Model):
    """Modelo para gestión de jornadas de recolección"""

    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('activa', 'Activa'),
        ('finalizada', 'Finalizada'),
        ('cancelada', 'Cancelada'),
    ]

    TIPO_MATERIAL_CHOICES = [
        ('plastico', 'Plástico'),
        ('vidrio', 'Vidrio'),
        ('organico', 'Orgánico'),
        ('metal', 'Metal'),
        ('papel', 'Papel'),
        ('mixto', 'Mixto'),
    ]

    titulo = models.CharField(
        max_length=200,
        validators=[RegexValidator(
            regex=rf'^(?!.*(?:;|\-\-|OR|AND|UNION|SELECT|INSERT|DELETE|UPDATE|DROP|EXEC|EXECUTE|xp_|sp_|0x)).*$',
            message='Caracteres sospechosos no permitidos.',
            code='sql_injection_blocked'
        )],
        help_text='Título de la jornada'
    )

    descripcion = models.TextField(
        validators=[RegexValidator(
            regex=rf'^(?!.*(?:;|\-\-|OR|AND|UNION|SELECT|INSERT|DELETE|UPDATE|DROP|EXEC|EXECUTE|xp_|sp_|0x)).*$',
            message='Caracteres sospechosos no permitidos.',
            code='sql_injection_blocked'
        )],
        help_text='Descripción detallada de la jornada (mínimo 10, máximo 500 caracteres)'
    )

    fecha = models.DateTimeField(help_text='Fecha y hora de la jornada')

    direccion = models.CharField(
        max_length=255,
        validators=[RegexValidator(
            regex=rf'^(?!.*(?:;|\-\-|OR|AND|UNION|SELECT|INSERT|DELETE|UPDATE|DROP|EXEC|EXECUTE|xp_|sp_|0x)).*$',
            message='Caracteres sospechosos no permitidos.',
            code='sql_injection_blocked'
        )],
        help_text='Punto de encuentro'
    )

    barrio = models.CharField(max_length=100, help_text='Barrio donde se realizará la jornada')

    tipo_material = models.CharField(
        max_length=20,
        choices=TIPO_MATERIAL_CHOICES,
        help_text='Tipo de materiales a recolectar'
    )

    cupo_maximo = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text='Cupo máximo de participantes (1-200)'
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente',
        help_text='Estado de la jornada'
    )

    id_organizador = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='jornadas_organizadas',
        help_text='Organizador asignado a la jornada'
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Jornada'
        verbose_name_plural = 'Jornadas'
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.titulo} - {self.barrio} ({self.fecha.strftime('%d/%m/%Y %H:%M')})"

    def clean(self):
        # RN1.1.1 — fecha y hora deben ser futuras
        if self.fecha and self.fecha <= timezone.now():
            raise ValidationError('La fecha y hora deben ser futuras al momento de la creación.')

        # RN1.1.2 — descripción: mínimo 10, máximo 500 caracteres
        if self.descripcion:
            desc = self.descripcion.strip()
            if len(desc) < 10:
                raise ValidationError('La descripción debe contener mínimo 10 caracteres.')
            if len(desc) > 500:
                raise ValidationError('La descripción no puede superar los 500 caracteres.')

        # RN1.1.2 — cupo máximo entre 1 y 200
        if self.cupo_maximo and (self.cupo_maximo < 1 or self.cupo_maximo > 200):
            raise ValidationError('El cupo máximo debe ser mayor a cero y no puede superar 200 personas.')

        # RN1.1.2 — unicidad barrio + fecha + hora
        if self.fecha and self.barrio:
            conflicto = Jornada.objects.filter(
                barrio__iexact=self.barrio,
                fecha=self.fecha,
                estado__in=['pendiente', 'activa']
            ).exclude(pk=self.pk if self.pk else None)
            if conflicto.exists():
                raise ValidationError(
                    'Ya existe una jornada activa en este barrio para esa fecha y hora.'
                )

    @property
    def inscritos_count(self):
        """Número de inscritos actuales."""
        return self.inscripciones.count()

    @property
    def cupo_disponible(self):
        """Indica si quedan lugares disponibles."""
        return self.inscritos_count < self.cupo_maximo

    @property
    def porcentaje_inscripcion(self):
        """Porcentaje del cupo ocupado (0-100)."""
        if not self.cupo_maximo:
            return 0
        return (self.inscritos_count / self.cupo_maximo) * 100


class Registro(models.Model):
    """Modelo para el registro de usuarios en el sistema CRM"""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='registro')

    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    barrio = models.CharField(max_length=100, blank=True, null=True, help_text='Barrio de residencia')

    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Registro'
        verbose_name_plural = 'Registros'
        ordering = ['-fecha_registro']

    def __str__(self):
        return f"{self.user.username} - {self.ciudad or 'Sin ciudad'}"


class Inscripcion(models.Model):
    """Modelo para inscripciones de residentes a jornadas"""
    residente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inscripciones')
    jornada = models.ForeignKey(Jornada, on_delete=models.CASCADE, related_name='inscripciones')
    fecha_inscripcion = models.DateTimeField(auto_now_add=True)
    asistencia = models.BooleanField(default=False, help_text='Indica si el residente asistió a la jornada')
    confirmada = models.BooleanField(default=False, help_text='Indica si la inscripción está confirmada')

    class Meta:
        verbose_name = 'Inscripción'
        verbose_name_plural = 'Inscripciones'
        unique_together = ('residente', 'jornada')
        ordering = ['-fecha_inscripcion']

    def __str__(self):
        return f"{self.residente.username} - {self.jornada.titulo} ({'Asistió' if self.asistencia else 'Pendiente'})"