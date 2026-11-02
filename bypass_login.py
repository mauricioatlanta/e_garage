from django.http import HttpResponseRedirect
from django.contrib.auth import get_user_model, login
from taller.models.empresa import Empresa

User = get_user_model()

def login_directo_dev(request):
    """Bypass de login para entorno de desarrollo local."""
    user = User.objects.filter(username__iexact='mauricioatlanta').first() or User.objects.filter(is_superuser=True).first()
    if not user:
        user = User.objects.create_superuser('mauricioatlanta', 'mauricioatlanta@gmail.com', 'admin1234')
    
    empresa = Empresa.objects.first()
    if not empresa:
        empresa = Empresa.objects.create(nombre='Atlanta Reciclajes', rut='77350892-5', pais='CL')

    user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, user)
    
    request.session['empresa_id'] = empresa.id
    request.session.save()
    
    response = HttpResponseRedirect('/cl/es/desarme/catalogo/')
    response.set_cookie(
        'sessionid',
        request.session.session_key,
        max_age=86400,
        httponly=True,
        secure=False,
        samesite='Lax'
    )
    return response

# Alias para compatibilidad con cualquier ruta previa en urls.py
auto_login_view = login_directo_dev
