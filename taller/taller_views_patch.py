from .models.taller_info import TallerInfo

# ...resto de imports...

# Solo usuarios staff pueden acceder
@user_passes_test(lambda u: u.is_staff)
def dashboard_suscripciones(request):
    empresas = sorted(Empresa.objects.all(), key=lambda e: e.fecha_expiracion)
    # Obtener nombre_taller para cada empresa si existe TallerInfo
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

# ...resto del archivo...
