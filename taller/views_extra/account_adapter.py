from allauth.account.adapter import DefaultAccountAdapter
from django.shortcuts import redirect
from django.urls import reverse

class CountryAwareAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        path = request.path
        # Detectar país por path
        if path.startswith('/cl/') or 'cl' in request.GET.get('country', ''):
            return reverse('chile:dashboard')
        if path.startswith('/us') or path.startswith('/usa') or 'us' in request.GET.get('country', '') or 'usa' in request.GET.get('country', ''):
            return reverse('usa:dashboard')
        country = request.session.get('country')
        if country == 'usa':
            return reverse('usa:dashboard')
        return reverse('chile:dashboard')
