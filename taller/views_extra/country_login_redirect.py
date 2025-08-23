from django.shortcuts import redirect
from django.urls import reverse

def post_activation_login_redirect(request):
    path = request.path
    if path.startswith('/cl/'):
        ns = 'chile'
    elif path.startswith('/us/'):
        ns = 'usa'
    else:
        ns = None
    if ns:
        try:
            return redirect(reverse(f'{ns}:account_login'))
        except Exception:
            pass
    return redirect(reverse('account_login'))
