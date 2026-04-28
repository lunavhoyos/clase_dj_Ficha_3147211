from django.contrib import admin
from .models import Registro

@admin.register(Registro)
class RegistroAdmin(admin.ModelAdmin):
    list_display = ('user', 'telefono', 'ciudad', 'fecha_registro')
    list_filter = ('fecha_registro', 'ciudad')
    search_fields = ('user__username', 'user__email', 'telefono')
    date_hierarchy = 'fecha_registro'
    ordering = ('-fecha_registro',)
    
    fieldsets = (
        ('Informacion de Usuario', {
            'fields': ('user',)
        }),
        ('Informacion de Contacto', {
            'fields': ('telefono', 'direccion', 'ciudad')
        }),
    )
