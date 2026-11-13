from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt
from taller.models.empresa import Empresa

def country_aware_login(request, *args, **kwargs):
    if request.user.is_authenticated:
        return redirect('/cl/es/workspace/')

    error = None
    if request.method == 'POST':
        login_val = request.POST.get('login', '').strip()
        pass_val = request.POST.get('password', '').strip()

        user = authenticate(request, username=login_val, password=pass_val)
        if not user and '@' in login_val:
            from django.contrib.auth import get_user_model
            U = get_user_model()
            u_obj = U.objects.filter(email__iexact=login_val).first()
            if u_obj:
                user = authenticate(request, username=u_obj.username, password=pass_val)

        if user:
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('/cl/es/workspace/')
        else:
            error = "Credenciales incorrectas. Verifica tu contraseña."

    return render(request, 'account/login.html', {'error_custom': error})
