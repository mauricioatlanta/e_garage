from django.contrib.auth.decorators import login_required

@login_required
def suscripcion_bloqueada(request):
    return render(request, "suscripcion_bloqueada.html", {
        "dias_restantes": 0,
        "empresa": getattr(request, "empresa", None),
    })

from django.shortcuts import render

def debug_cliente_autocomplete(request):
    return render(request, 'debug_autocomplete_cliente.html')

# --- Vistas de administración de suscripciones ---
from django.contrib.auth.decorators import user_passes_test
from django.utils.timezone import now
from django.shortcuts import get_object_or_404, redirect
from .models.empresa import Empresa
from .models.taller_info import TallerInfo

# Solo usuarios staff pueden acceder

# Solo usuarios staff pueden acceder
@user_passes_test(lambda u: u.is_staff)
def dashboard_suscripciones(request):
    empresas = sorted(Empresa.objects.all(), key=lambda e: e.fecha_expiracion)
    empresas_con_taller = []
    for empresa in empresas:
        nombre_taller = None
        if hasattr(empresa.usuario_admin, 'taller_info'):
            nombre_taller = empresa.usuario_admin.taller_info.nombre_taller
        empresas_con_taller.append({
            'empresa': empresa,
            'nombre_taller': nombre_taller
        })
    return render(request, 'admin/suscripciones_dashboard.html', {'empresas_con_taller': empresas_con_taller})

@user_passes_test(lambda u: u.is_staff)
def renovar_empresa(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    if request.method == 'POST':
        empresa.fecha_inicio = now()
        empresa.suscripcion_activa = True
        empresa.save()
    return redirect('dashboard_suscripciones')
