

from django.shortcuts import render
from django.utils import translation

def bienvenida_usa(request):
    translation.activate('en')
    return render(request, 'onboarding/bienvenida_usa.html')
