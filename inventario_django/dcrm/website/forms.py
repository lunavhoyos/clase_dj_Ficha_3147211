from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Registro

class RegistroForm(UserCreationForm):
    """Formulario para el registro de nuevos usuarios"""
    
    # Campos de usuario
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
    
    # Campos adicionales esenciales
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
        # Personalizar mensajes de ayuda
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
        
        # Agregar clases a los campos de contrasena
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
    
    def save(self, commit=True):
        user = super(RegistroForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            
            # Crear el registro asociado
            Registro.objects.create(
                user=user,
                telefono=self.cleaned_data.get('telefono', ''),
                direccion=self.cleaned_data.get('direccion', ''),
                ciudad=self.cleaned_data.get('ciudad', '')
            )
        
        return user
