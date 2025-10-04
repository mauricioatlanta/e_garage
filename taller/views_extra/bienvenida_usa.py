from django.shortcuts import render
from django.utils import translation


def bienvenida_usa(request):
    # Force English language for USA page
    translation.activate("en")
    request.LANGUAGE_CODE = "en"
    
    # Create context with language code
    context = {
        'LANGUAGE_CODE': 'en'
    }
    
    return render(request, "onboarding/bienvenida_usa.html", context)
