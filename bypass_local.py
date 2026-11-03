from django.http import HttpResponseRedirect
from django.contrib.auth import get_user_model, login
from taller.models.empresa import Empresa

User = get_user_model()

def login_rapido(request):
    user = User.objects.filter(username__iexact='mauricioatlanta').first() or User.objects.first()
    empresa = Empresa.objects.first()
    
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, user)
    
    if empresa:
        request.session['empresa_id'] = empresa.id
        request.session['empresa_activa_id'] = empresa.id
    request.session.save()
    
    response = HttpResponseRedirect('/cl/es/reportes/')
    response.set_cookie(
        'sessionid',
        request.session.session_key,
        max_age=86400 * 30,
        httponly=True,
        secure=False,
        samesite='Lax'
    )
    return response
