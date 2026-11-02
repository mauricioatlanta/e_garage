from django.shortcuts import render
from django.urls import reverse

from taller.qa_control.auth import control_tower_required


@control_tower_required
def admin_control_center(request):
    cards = [
        {
            "icon": "QA",
            "title": "Torre de Control QA",
            "description": "Selecciona país, rubro y entorno para revisar eGarage como suscriptor.",
            "url": reverse("qa_control:control"),
        },
        {
            "icon": "IV",
            "title": "Inteligencia de Visitas",
            "description": "Analiza tráfico público, campañas, embudos y conversiones atribuidas.",
            "url": reverse("admin_visitas"),
        },
        {
            "icon": "GS",
            "title": "Gestión de Suscriptores",
            "description": "Consulta empresas, planes, estados de suscripción y datos comerciales.",
            "url": reverse("admin_suscriptores"),
        },
    ]
    return render(request, "admin/control.html", {"cards": cards})
