from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Registro, Jornada


class JornadaForm(forms.ModelForm):
    """Formulario ModelForm para la entidad Jornada"""

    class Meta:
        model = Jornada
        fields = ['titulo', 'descripcion', 'fecha', 'direccion', 'barrio', 'tipo_material', 'cupo_maximo', 'estado', 'id_organizador']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título de la jornada'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción de la jornada (mínimo 10 caracteres)',
                'rows': 3
            }),
            'fecha': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'direccion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Punto de encuentro'
            }),
            'barrio': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Barrio donde se realizará la jornada'
            }),
            'tipo_material': forms.Select(attrs={
                'class': 'form-select'
            }),
            'cupo_maximo': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 200
            }),
            'estado': forms.Select(attrs={
                'class': 'form-select'
            }),
            'id_organizador': forms.Select(attrs={
                'class': 'form-select'
            }),
        }

    def __init__(self, *args, **kwargs):
        super(JornadaForm, self).__init__(*args, **kwargs)
        self.fields['id_organizador'].queryset = User.objects.filter(groups__name__in=['ADMIN', 'ORGANIZADOR']).distinct()

    def clean_fecha(self):
        fecha = self.cleaned_data.get('fecha')
        if fecha and fecha <= timezone.now():
            raise forms.ValidationError('La fecha y hora deben ser futuras.')
        return fecha

    def clean_descripcion(self):
        descripcion = self.cleaned_data.get('descripcion')
        if descripcion and len(descripcion.strip()) < 10:
            raise forms.ValidationError('La descripción debe tener al menos 10 caracteres.')
        return descripcion

    def clean_cupo_maximo(self):
        cupo_maximo = self.cleaned_data.get('cupo_maximo')
        if cupo_maximo is not None and (cupo_maximo < 1 or cupo_maximo > 200):
            raise forms.ValidationError('El cupo máximo debe estar entre 1 y 200 personas.')
        return cupo_maximo


class RegistroForm(UserCreationForm):
    """Formulario para el registro de nuevos usuarios"""

    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre',
            'autofocus': True
        })
    )

    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Apellido'
        })
    )

    email = forms.EmailField(
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Correo electronico'
        })
    )

    telefono = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Telefono (opcional)'
        })
    )

    direccion = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Direccion (opcional)'
        })
    )

    ciudad = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ciudad (opcional)'
        })
    )

    barrio = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Barrio de residencia (Obligatorio)'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de usuario'
            }),
        }

    def __init__(self, *args, **kwargs):
        super(RegistroForm, self).__init__(*args, **kwargs)
        self.fields['username'].help_text = 'Requerido. 150 caracteres o menos. Solo letras, numeros y @/./+/-/_'
        self.fields['password1'].help_text = '''
            <ul class="mb-0">
                <li>Tu contrasena no puede ser muy similar a tu informacion personal.</li>
                <li>Tu contrasena debe contener al menos 8 caracteres.</li>
                <li>Tu contrasena no puede ser una contrasena comunmente usada.</li>
                <li>Tu contrasena no puede ser completamente numerica.</li>
            </ul>
        '''
        self.fields['password2'].help_text = 'Para verificar, ingrese la misma contrasena anterior.'

        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        user = super(RegistroForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            user.save()

            from django.contrib.auth.models import Group
            rol_nombre = 'RESIDENTE'
            group, created = Group.objects.get_or_create(name=rol_nombre)
            user.groups.add(group)

            Registro.objects.create(
                user=user,
                telefono=self.cleaned_data.get('telefono', ''),
                direccion=self.cleaned_data.get('direccion', ''),
                ciudad=self.cleaned_data.get('ciudad', ''),
                barrio=self.cleaned_data.get('barrio', '')
            )

        return user