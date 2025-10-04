import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.shortcuts import render

from taller.models.empresa import Empresa
from taller.models.perfil_usuario import PerfilUsuario
from taller.models.tecnico import Tecnico


@login_required
def configuracion_empresa(request):
    """
    Vista principal de configuración del taller
    """
    try:
        empresa = request.user.empresa
    except Empresa.DoesNotExist:
        empresa, created = Empresa.objects.get_or_create(
            user=request.user,
            defaults={
                "nombre_taller": f"Taller de {request.user.username}",
                "telefono": "",
                "email": request.user.email or "",
                "direccion": "",
            },
        )
        # Crear perfil básico sin relación a empresa
        perfil, perfil_created = PerfilUsuario.objects.get_or_create(
            user=request.user, defaults={"pais": "CL"}
        )
        if perfil_created:
            messages.info(request, "✅ Se ha creado un perfil básico para tu usuario.")

    if request.method == "POST":
        if "actualizar_empresa" in request.POST:
            nombre_taller = request.POST.get("nombre_taller", "").strip()
            empresa_nombre = request.POST.get("empresa_nombre", "").strip()
            telefono = request.POST.get("telefono", "").strip()
            email = request.POST.get("email", "").strip()
            direccion = request.POST.get("direccion", "").strip()

            if nombre_taller:
                empresa.nombre_taller = nombre_taller
                empresa.empresa = empresa_nombre
                empresa.telefono = telefono
                empresa.email = email
                empresa.direccion = direccion

                # Manejar logo
                if "logo" in request.FILES:
                    logo_file = request.FILES["logo"]
                    if logo_file.size > 5 * 1024 * 1024:  # 5MB máximo
                        messages.error(request, "❌ El logo no puede exceder 5MB.")
                    elif not logo_file.content_type.startswith("image/"):
                        messages.error(request, "❌ El archivo debe ser una imagen.")
                    else:
                        # Eliminar logo anterior si existe
                        if empresa.logo:
                            if default_storage.exists(empresa.logo.name):
                                default_storage.delete(empresa.logo.name)

                        # Asignar nuevo logo
                        empresa.logo = logo_file
                        messages.success(request, "📷 Logo actualizado exitosamente.")

                empresa.save()
                messages.success(
                    request, "✅ Información de la empresa actualizada exitosamente."
                )
            else:
                messages.error(request, "❌ El nombre del taller es obligatorio.")

    # Obtener estadísticas
    tecnicos_total = Tecnico.objects.filter(empresa=empresa).count()
    tecnicos_activos = Tecnico.objects.filter(empresa=empresa, activo=True).count()
    tecnicos_inactivos = tecnicos_total - tecnicos_activos

    from taller.models.documento import Documento

    documentos_total = Documento.objects.filter(empresa=empresa).count()

    context = {
        "empresa": empresa,
        "stats": {
            "tecnicos_total": tecnicos_total,
            "tecnicos_activos": tecnicos_activos,
            "tecnicos_inactivos": tecnicos_inactivos,
            "documentos_total": documentos_total,
        },
    }

    return render(request, "taller/configuracion/empresa_simple.html", context)


@login_required
def configuracion_tecnicos(request):
    """
    Vista para gestionar los técnicos del taller
    """
    try:
        empresa = request.user.empresa
    except Empresa.DoesNotExist:
        # Si no tiene empresa, crear una básica
        empresa, created = Empresa.objects.get_or_create(
            user=request.user,
            defaults={
                "nombre_taller": f"Taller de {request.user.username}",
                "telefono": "",
                "email": request.user.email or "",
                "direccion": "",
            },
        )
        messages.info(request, "✅ Se ha creado un perfil básico para tu usuario.")

    if request.method == "POST":
        if "action" in request.POST and request.POST["action"] == "add":
            nombre = request.POST.get("nombre", "").strip()
            apellido = request.POST.get("apellido", "").strip()
            email = request.POST.get("email", "").strip()
            telefono = request.POST.get("telefono", "").strip()
            especialidad = request.POST.get("especialidad", "").strip()

            # Combinar nombre y apellido
            nombre_completo = f"{nombre} {apellido}".strip()

            # Validar campos obligatorios
            if not nombre or len(nombre.strip()) < 2:
                messages.error(
                    request,
                    "❌ El nombre del técnico debe tener al menos 2 caracteres.",
                )
            elif not apellido or len(apellido.strip()) < 2:
                messages.error(
                    request,
                    "❌ El apellido del técnico debe tener al menos 2 caracteres.",
                )
            elif Tecnico.objects.filter(
                empresa=empresa, nombre__iexact=nombre_completo
            ).exists():
                messages.error(
                    request,
                    f'❌ Ya existe un técnico con el nombre "{nombre_completo}" en tu taller.',
                )
            else:
                Tecnico.objects.create(
                    empresa=empresa,
                    nombre=nombre_completo,
                    telefono=telefono,
                    direccion=especialidad,  # Usar especialidad como dirección
                    activo=True,
                )
                messages.success(
                    request, f'✅ Técnico "{nombre_completo}" agregado exitosamente.'
                )

        elif "desactivar_tecnico" in request.POST:
            tecnico_id = request.POST.get("tecnico_id")
            tecnico = Tecnico.objects.filter(id=tecnico_id, empresa=empresa).first()
            if tecnico:
                tecnico.activo = False
                tecnico.save()
                messages.success(
                    request,
                    f'❌ Técnico "{tecnico.nombre}" desactivado. Ya no aparecerá en formularios nuevos.',
                )

        elif "activar_tecnico" in request.POST:
            tecnico_id = request.POST.get("tecnico_id")
            tecnico = Tecnico.objects.filter(id=tecnico_id, empresa=empresa).first()
            if tecnico:
                tecnico.activo = True
                tecnico.save()
                messages.success(request, f'✅ Técnico "{tecnico.nombre}" reactivado.')

        elif "editar_tecnico" in request.POST:
            tecnico_id = request.POST.get("tecnico_id")
            nuevo_nombre = request.POST.get("nuevo_nombre", "").strip()
            nuevo_telefono = request.POST.get("nuevo_telefono", "").strip()
            nueva_direccion = request.POST.get("nueva_direccion", "").strip()
            tecnico = Tecnico.objects.filter(id=tecnico_id, empresa=empresa).first()

            # Validar campos obligatorios
            if not tecnico:
                messages.error(request, "❌ Técnico no encontrado.")
            elif not nuevo_nombre or len(nuevo_nombre) < 2:
                messages.error(
                    request, "❌ El nombre debe tener al menos 2 caracteres."
                )
            elif not nuevo_telefono or len(nuevo_telefono.strip()) < 8:
                messages.error(
                    request,
                    "❌ El teléfono es obligatorio y debe tener al menos 8 caracteres.",
                )
            elif not re.match(r"^[\d\s\-\+\(\)]+$", nuevo_telefono):
                messages.error(
                    request,
                    "❌ Formato de teléfono inválido. Solo números, espacios, guiones, + y paréntesis.",
                )
            elif (
                Tecnico.objects.filter(empresa=empresa, nombre__iexact=nuevo_nombre)
                .exclude(id=tecnico_id)
                .exists()
            ):
                messages.error(
                    request,
                    f'❌ Ya existe otro técnico con el nombre "{nuevo_nombre}".',
                )
            else:
                nombre_anterior = tecnico.nombre
                tecnico.nombre = nuevo_nombre
                tecnico.telefono = nuevo_telefono
                tecnico.direccion = nueva_direccion
                tecnico.save()
                messages.success(
                    request, f'✏️ Técnico "{nombre_anterior}" actualizado exitosamente.'
                )

        elif "action" in request.POST and request.POST["action"] == "delete":
            tecnico_id = request.POST.get("tecnico_id")
            tecnico = Tecnico.objects.filter(id=tecnico_id, empresa=empresa).first()
            if tecnico:
                # Verificar si el técnico tiene documentos asociados
                from taller.models.documento import Documento

                documentos_asociados = Documento.objects.filter(tecnico=tecnico).count()
                if documentos_asociados > 0:
                    messages.warning(
                        request,
                        f'⚠️ No se puede eliminar "{tecnico.nombre}" porque tiene {documentos_asociados} documentos asociados. Se ha desactivado en su lugar.',
                    )
                    tecnico.activo = False
                    tecnico.save()
                else:
                    nombre = tecnico.nombre
                    tecnico.delete()
                    messages.success(
                        request, f'🗑️ Técnico "{nombre}" eliminado completamente.'
                    )

        # Redirección dinámica basada en el país del usuario
        from django.shortcuts import redirect

        if hasattr(request.user, "empresa") and request.user.empresa.pais == "US":
            return redirect("/us/configuracion/tecnicos/")
        else:
            return redirect("/cl/configuracion/tecnicos/")

    # Obtener técnicos ordenados: primero los activos, luego por nombre
    tecnicos = Tecnico.objects.filter(empresa=empresa).order_by("-activo", "nombre")
    tecnicos_activos = tecnicos.filter(activo=True).count()
    tecnicos_inactivos = tecnicos.filter(activo=False).count()

    return render(
        request,
        "taller/configuracion/tecnicos.html",
        {
            "tecnicos": tecnicos,
            "empresa": empresa,
            "stats": {
                "total": tecnicos.count(),
                "activos": tecnicos_activos,
                "inactivos": tecnicos_inactivos,
            },
        },
    )
