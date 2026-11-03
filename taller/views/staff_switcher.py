import re
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from taller.models.empresa import Empresa

@csrf_exempt
def switch_support_environment(request):
    if not (request.user.is_authenticated and request.user.is_superuser):
        return redirect("/cl/es/accounts/login/")

    if request.method == "POST":
        country = (request.POST.get("country") or request.POST.get("pais") or "us").lower().strip()
        selected = request.POST.getlist("rubros")
        rubro = selected[0] if selected else "TALLER"

        # Asignar la empresa de USA limpia
        if country == "us":
            emp = Empresa.objects.filter(pais="US").first()
            if not emp:
                emp = Empresa.objects.create(nombre_taller="eGarage Workshop USA", rut="US-999999", pais="US")
        else:
            emp = Empresa.objects.filter(pais="CL").first() or Empresa.objects.filter(id=1).first()

        if emp and hasattr(request.user, "perfilusuario"):
            p = request.user.perfilusuario
            p.empresa = emp
            p.save()

        # Grabar variables en sesión
        request.session["support_country"] = country
        request.session["modo_soporte_pais"] = country
        request.session["support_rubro"] = rubro
        request.session["modo_soporte_rubros"] = selected
        request.session["modo_soporte_activo"] = True
        request.session["django_language"] = "es"
        if emp:
            request.session["empresa_id"] = emp.id
        request.session.modified = True

        if "desarmaduria" in [r.lower() for r in selected]:
            target = f"/{country}/es/desarme/vehiculos/"
        else:
            target = f"/{country}/es/reportes/"

        response = redirect(target)
        response.set_cookie("django_language", "es", max_age=365*24*60*60, domain=".egarage.cl", path="/")
        return response

    return redirect("/us/es/reportes/")
