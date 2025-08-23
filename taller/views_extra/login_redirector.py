from django.shortcuts import redirect
from django.urls import reverse

def login_redirector(request):
    path = request.path
    # Detectar país por path
    if path.startswith('/cl/') or 'cl' in request.GET.get('country', ''):
        return redirect(reverse('chile:account_login'))
    if path.startswith('/us') or path.startswith('/usa') or 'us' in request.GET.get('country', '') or 'usa' in request.GET.get('country', ''):
        return redirect(reverse('usa:account_login'))
    # Fallback: intentar detectar por sesión o default a Chile
    country = request.session.get('country')
    if country == 'us' or country == 'usa':
        return redirect(reverse('usa:account_login'))
    return redirect(reverse('chile:account_login'))
