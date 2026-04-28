from django.db import models
from django.contrib.auth.models import User

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
