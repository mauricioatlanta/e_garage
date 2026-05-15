"""
Vista para listar todas las credenciales de usuarios registrados en eGarage.
Accesible desde: /admin/credenciales-usuarios/
"""

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.utils import timezone

from taller.models.empresa import Empresa
from taller.models.suscripcion import Suscripcion
from taller.models.trial import TrialRegistro


@staff_member_required
def listar_credenciales_usuarios(request):
    """
    Lista todas las credenciales de usuarios registrados en eGarage.
    Muestra: username, email, empresa, país, plan, y estado de suscripción.
    """

    def obtener_nombre_pais(codigo):
        paises = {
            "CL": "Chile",
            "US": "Estados Unidos",
            "MX": "México",
            "PE": "Perú",
            "CO": "Colombia",
            "EC": "Ecuador",
            "BR": "Brasil",
            "VE": "Venezuela",
        }
        return paises.get(codigo, codigo)

    def formatear_fecha(fecha):
        if not fecha:
            return "N/A"
        if hasattr(fecha, "strftime"):
            return fecha.strftime("%Y-%m-%d %H:%M:%S")
        return str(fecha)

    output = []
    output.append("=" * 80)
    output.append("🔐 CREDENCIALES DE USUARIOS REGISTRADOS EN eGARAGE")
    output.append("=" * 80)
    output.append(f"Fecha de consulta: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output.append("")
    output.append("⚠️  NOTA: Las contraseñas están hasheadas por seguridad.")
    output.append(
        "    Para resetear una contraseña, usa: python manage.py changepassword <username>"
    )
    output.append("")

    # Obtener todos los usuarios (excluyendo staff/superuser a menos que se especifique)
    mostrar_staff = request.GET.get("incluir_staff", "false").lower() == "true"

    if mostrar_staff:
        usuarios = User.objects.all().order_by("date_joined")
        output.append("📋 TODOS LOS USUARIOS (incluyendo staff/superuser)")
    else:
        usuarios = User.objects.filter(is_staff=False, is_superuser=False).order_by("date_joined")
        output.append("📋 USUARIOS REGISTRADOS (excluyendo staff/superuser)")

    output.append("-" * 80)
    output.append(f"Total usuarios: {usuarios.count()}")
    output.append("")

    # Agrupar por país
    usuarios_por_pais = {}
    usuarios_sin_empresa = []

    for user in usuarios:
        try:
            if hasattr(user, "empresa") and user.empresa:
                pais = user.empresa.pais
                if pais not in usuarios_por_pais:
                    usuarios_por_pais[pais] = []
                usuarios_por_pais[pais].append(user)
            else:
                usuarios_sin_empresa.append(user)
        except:
            usuarios_sin_empresa.append(user)

    # Mostrar usuarios por país
    for pais_codigo in sorted(usuarios_por_pais.keys()):
        pais_nombre = obtener_nombre_pais(pais_codigo)
        usuarios_pais = usuarios_por_pais[pais_codigo]

        output.append("=" * 80)
        output.append(f"🌍 PAÍS: {pais_nombre} ({pais_codigo})")
        output.append(f"Total usuarios: {len(usuarios_pais)}")
        output.append("=" * 80)

        for idx, user in enumerate(usuarios_pais, 1):
            output.append(f"\n{idx}. 👤 USUARIO: {user.username}")
            output.append(f"   📧 Email: {user.email}")
            output.append(f"   👤 Nombre: {user.first_name} {user.last_name}".strip() or "N/A")
            output.append(f"   📅 Fecha Registro: {formatear_fecha(user.date_joined)}")
            output.append(f"   ✅ Activo: {'Sí' if user.is_active else 'No'}")

            # Información de empresa
            try:
                if hasattr(user, "empresa") and user.empresa:
                    empresa = user.empresa
                    output.append(f"   🏢 Empresa: {empresa.nombre_taller}")
                    output.append(f"   📋 Plan: {empresa.plan}")
                    output.append(f"   💰 Moneda: {empresa.moneda}")
                    output.append(f"   📍 Dirección: {empresa.direccion or 'N/A'}")
                    output.append(f"   📞 Teléfono: {empresa.telefono or 'N/A'}")
                    output.append(
                        f"   ✅ Suscripción Activa: {'Sí' if empresa.suscripcion_activa else 'No'}"
                    )
                    output.append(f"   📅 Fecha Inicio: {formatear_fecha(empresa.fecha_inicio)}")
                    output.append(f"   📅 Fecha Fin: {formatear_fecha(empresa.fecha_fin)}")
                    if hasattr(empresa, "dias_restantes"):
                        output.append(f"   ⏰ Días Restantes: {empresa.dias_restantes}")
            except:
                output.append(f"   ⚠️  Sin empresa asociada")

            # Información de suscripción
            try:
                if hasattr(user, "suscripcion") and user.suscripcion:
                    susc = user.suscripcion
                    estado = "✅ ACTIVA" if susc.activa else "❌ INACTIVA"
                    vencida = susc.esta_vencida() if hasattr(susc, "esta_vencida") else False
                    if vencida:
                        estado = "❌ VENCIDA"
                    es_trial = (
                        susc.es_prueba() if hasattr(susc, "es_prueba") else susc.tipo == "trial"
                    )
                    output.append(f"   📋 Suscripción: {estado}")
                    output.append(f"   📋 Tipo: {susc.tipo} {'(TRIAL)' if es_trial else ''}")
                    output.append(f"   📅 Fecha Inicio: {formatear_fecha(susc.fecha_inicio)}")
                    output.append(f"   📅 Fecha Fin: {formatear_fecha(susc.fecha_fin)}")
            except:
                output.append(f"   ⚠️  Sin suscripción asociada")

            # Información de trial
            try:
                trial = TrialRegistro.objects.filter(email=user.email).first()
                if trial:
                    estado_trial = "✅ ACTIVA" if trial.prueba_activa else "❌ INACTIVA"
                    output.append(f"   🧪 Trial: {estado_trial}")
                    output.append(
                        f"   📅 Fecha Registro Trial: {formatear_fecha(trial.fecha_registro)}"
                    )
                    output.append(
                        f"   📅 Fecha Activación: {formatear_fecha(trial.fecha_activacion)}"
                    )
            except:
                pass

            output.append("")

    # Usuarios sin empresa
    if usuarios_sin_empresa:
        output.append("=" * 80)
        output.append("⚠️  USUARIOS SIN EMPRESA ASOCIADA")
        output.append("=" * 80)
        for idx, user in enumerate(usuarios_sin_empresa, 1):
            output.append(f"\n{idx}. 👤 {user.username}")
            output.append(f"   📧 Email: {user.email}")
            output.append(f"   📅 Fecha Registro: {formatear_fecha(user.date_joined)}")
            output.append(f"   ✅ Activo: {'Sí' if user.is_active else 'No'}")
        output.append("")

    # Resumen final
    output.append("=" * 80)
    output.append("📊 RESUMEN FINAL")
    output.append("=" * 80)
    output.append(f"Total usuarios registrados: {usuarios.count()}")
    output.append(f"Usuarios con empresa: {sum(len(u) for u in usuarios_por_pais.values())}")
    output.append(f"Usuarios sin empresa: {len(usuarios_sin_empresa)}")
    output.append("")
    output.append("Países con usuarios:")
    for pais_codigo in sorted(usuarios_por_pais.keys()):
        pais_nombre = obtener_nombre_pais(pais_codigo)
        count = len(usuarios_por_pais[pais_codigo])
        output.append(f"  - {pais_nombre} ({pais_codigo}): {count} usuarios")
    output.append("")
    output.append("=" * 80)
    output.append("✅ Reporte completado")
    output.append("=" * 80)
    output.append("")
    output.append("💡 Para resetear una contraseña:")
    output.append("   python manage.py changepassword <username>")
    output.append("")
    output.append("💡 Para ver este reporte incluyendo staff:")
    output.append("   /admin/credenciales-usuarios/?incluir_staff=true")
    output.append("=" * 80)

    # Retornar como respuesta HTTP con formato de texto plano
    response = HttpResponse("\n".join(output), content_type="text/plain; charset=utf-8")
    return response
