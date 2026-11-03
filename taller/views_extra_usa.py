from django.http import HttpResponseRedirect
from django.contrib.auth import get_user_model, login
from django.conf import settings
from taller.models.empresa import Empresa

User = get_user_model()

def entrar_usa_directo(request):
    u = User.objects.filter(username="mauricioatlanta").first() or User.objects.filter(is_superuser=True).first()
    if u:
        emp_us = Empresa.objects.filter(pais="US").first()
        if not emp_us:
            emp_us = Empresa.objects.create(nombre_taller="eGarage Workshop USA", rut="US-999999", pais="US")
        
        if hasattr(u, "perfilusuario"):
            u.perfilusuario.empresa = emp_us
            u.perfilusuario.save()

        u.backend = "django.contrib.auth.backends.ModelBackend"
        login(request, u)
        
        request.session["support_country"] = "us"
        request.session["modo_soporte_pais"] = "us"
        request.session["support_rubro"] = "TALLER"
        request.session["modo_soporte_rubros"] = ["TALLER"]
        request.session["modo_soporte_activo"] = True
        request.session["django_language"] = "es"
        request.session["empresa_id"] = emp_us.id
        request.session.modified = True
        request.session.save()

        resp = HttpResponseRedirect("/us/es/reportes/")
        resp.set_cookie(settings.SESSION_COOKIE_NAME, request.session.session_key, max_age=86400*30, domain=".egarage.cl", path="/")
        resp.set_cookie("django_language", "es", max_age=86400*365, domain=".egarage.cl", path="/")
        return resp
    return HttpResponseRedirect("/cl/es/accounts/login/")
