from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from taller.utils.country_config import get_country_config


@login_required
def signup_success_view(request):
    """
    Vista de éxito después del registro.
    Muestra información sobre el trial de 30 días y los pasos siguientes.
    """
    # Obtener información del país desde la sesión o desde la empresa del usuario
    country_code = "CL"  # Default

    if hasattr(request.user, "empresa") and request.user.empresa:
        country_code = request.user.empresa.pais or "CL"
    elif "country_config" in request.session:
        country_code = request.session.get("country_config", {}).get("code", "CL")

    # Obtener configuración del país
    country_config = get_country_config(country_code)

    context = {
        "page_title": "¡Registro Exitoso! | eGarage",
        "country_config": country_config,
        "country_code": country_code,
    }

    return render(request, "account/signup_success.html", context)



