from django.shortcuts import render
from django.contrib.auth import

# Create your views here.

def home(request):
    return render(request, 'home.html', {})

