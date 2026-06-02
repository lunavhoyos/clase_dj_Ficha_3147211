import json
import os
from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Registro
from django.contrib.auth.models import User

RECORDS_FILE = os.path.join(settings.BASE_DIR, 'records.json')

def sync_records_to_json():
    registros = Registro.objects.all().select_related('user')
    lista = []
    for reg in registros:
        lista.append({
            'id': reg.id,
            'username': reg.user.username,
            'first_name': reg.user.first_name or '',
            'last_name': reg.user.last_name or '',
            'email': reg.user.email or '',
            'telefono': reg.telefono or '',
            'ciudad': reg.ciudad or '',
            'direccion': reg.direccion or '',
            'fecha_registro': reg.fecha_registro.strftime('%d/%m/%Y %H:%M') if reg.fecha_registro else '',
        })
    with open(RECORDS_FILE, 'w', encoding='utf-8') as f:
        json.dump({'registros': lista}, f, ensure_ascii=False, indent=2)

@receiver(post_save, sender=Registro)
@receiver(post_save, sender=User)
def on_model_save(sender, **kwargs):
    sync_records_to_json()

@receiver(post_delete, sender=Registro)
@receiver(post_delete, sender=User)
def on_model_delete(sender, **kwargs):
    sync_records_to_json()
