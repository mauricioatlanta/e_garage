from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import activate, get_language
from django.views.decorators.http import require_POST

from taller.forms.onboarding import (
    OnboardingIdentidadForm,
    OnboardingFiscalForm,
    OnboardingContactoForm,
)
from taller.forms.tecnico import TecnicoForm
from taller.models.clientes import Cliente
from taller.models.configuracion import ConfiguracionEmpresa
from taller.models.documento import Documento
from taller.models.empresa import Empresa
from taller.models.tecnico import Tecnico
from taller.models.vehiculos import Vehiculo
from taller.utils.country_config import get_country_config
from taller.templatetags.role_tags import is_owner
from taller.utils.empresa import get_active_empresa
from taller.services.company_defaults_service import CompanyDefaultsService


def owner_required(view_func):
    """Decorator to ensure only owners can access onboarding"""
    return user_passes_test(lambda u: is_owner(u), login_url="taller:dashboard")(view_func)


@login_required
@owner_required
def onboarding_wizard(request, step=None):
    """
    Vista principal del wizard de onboarding
    """
    try:
        empresa = get_active_empresa(request)
    except Exception:
        messages.error(request, "No se encontró una empresa activa.")
        return redirect("taller:dashboard")

    if not empresa:
        messages.error(request, "Debes configurar tu empresa primero.")
        try:
            return redirect("taller:configuracion")
        except:
            return redirect("/configuracion/")

    # Si ya completó el onboarding, redirigir a Ajustes
    if getattr(empresa, "onboarding_completado", False):
        return redirect("taller:company_settings")

    if step == "identidad" and getattr(empresa, "onboarding_step", 1) > 1:
        return redirect("taller:company_settings")

    # Mapear nombres de pasos a números (wizard simplificado)
    step_map = {
        "identidad": 1,
        "fiscal": 2,
        "finalizar": 3,
    }

    # Si no se especifica paso en la URL, usar el paso guardado en la empresa
    if step is None:
        paso_actual = getattr(empresa, "onboarding_step", 1)
    else:
        paso_actual = step_map.get(step, getattr(empresa, "onboarding_step", 1))

    # SEGURIDAD: No permitir saltar pasos adelante si el anterior no está completo
    if paso_actual > getattr(empresa, "onboarding_step", 1):
        # Redirigir al paso que realmente le corresponde
        rev_step_map = {v: k for k, v in step_map.items()}
        return redirect(
            "taller:onboarding_step",
            step=rev_step_map.get(getattr(empresa, "onboarding_step", 1), "identidad"),
        )

    # Compatibilidad: si llegan pasos antiguos, redirigir al flujo simplificado
    if step in {"contacto", "equipo"}:
        return redirect("taller:onboarding_step", step="finalizar")

    # Determinar template según paso
    templates = {
        1: "onboarding/paso_identidad.html",
        2: "onboarding/paso_fiscal.html",
        3: "onboarding/paso_finalizar.html",
    }

    template = templates.get(paso_actual, "onboarding/paso_identidad.html")

    # Configurar país e idioma
    country_config = get_country_config(empresa.pais)
    activate(country_config.get("lang", "es"))

    # Preparar contexto según paso
    context = {
        "empresa": empresa,
        "paso_actual": paso_actual,
        "total_pasos": 3,
        "progreso": (paso_actual / 3) * 100,
        "country_config": country_config,
    }

    # Agregar formularios según paso
    if paso_actual == 1:
        context["form"] = OnboardingIdentidadForm(instance=empresa)
    elif paso_actual == 2:
        config, _ = ConfiguracionEmpresa.objects.get_or_create(empresa=empresa)
        context["form"] = OnboardingFiscalForm(instance=config)
        context["config"] = config

    return render(request, template, context)


@login_required
@owner_required
@require_POST
def onboarding_guardar_paso(request, paso):
    """
    Guarda el progreso de un paso específico del onboarding con validación de formularios
    """
    try:
        empresa = get_active_empresa(request)
    except Exception:
        return JsonResponse({"success": False, "error": "Empresa no encontrada"})

    if not empresa:
        return JsonResponse({"success": False, "error": "Empresa no encontrada"})

    # SEGURIDAD: Validar que el paso que intenta guardar es el que le corresponde o anterior
    if paso > empresa.onboarding_step:
        return JsonResponse({"success": False, "message": "No puedes saltar pasos."})

    try:
        with transaction.atomic():
            if paso == 1:  # Identidad de la empresa
                form = OnboardingIdentidadForm(request.POST, request.FILES, instance=empresa)
                if form.is_valid():
                    form.save()

                    CompanyDefaultsService.apply_defaults_to_empresa(empresa, commit=True)

                    if empresa.onboarding_step == 1:
                        empresa.onboarding_step = 2
                        empresa.save(update_fields=["onboarding_step"])
                    return JsonResponse(
                        {
                            "success": True,
                            "next_step": 2,
                            "next_step_url": reverse(
                                "taller:onboarding_step", kwargs={"step": "fiscal"}
                            ),
                            "message": "Información básica guardada correctamente",
                        }
                    )
                return JsonResponse({"success": False, "errors": form.errors})

            elif paso == 2:  # Configuración fiscal
                config, _ = ConfiguracionEmpresa.objects.get_or_create(empresa=empresa)
                form = OnboardingFiscalForm(request.POST, instance=config)
                if form.is_valid():
                    form.save()

                    CompanyDefaultsService.apply_defaults_to_configuracion(
                        config, empresa=empresa, commit=True
                    )

                    if empresa.onboarding_step == 2:
                        empresa.onboarding_step = 3
                        empresa.save(update_fields=["onboarding_step"])
                    return JsonResponse(
                        {
                            "success": True,
                            "next_step": 3,
                            "next_step_url": reverse(
                                "taller:onboarding_step", kwargs={"step": "finalizar"}
                            ),
                            "message": "Configuración fiscal guardada",
                        }
                    )
                return JsonResponse({"success": False, "errors": form.errors})

            elif paso == 3:  # Finalizar
                empresa.onboarding_completado = True
                empresa.onboarding_completed_at = timezone.now()
                empresa.save(update_fields=["onboarding_completado", "onboarding_completed_at"])
                return JsonResponse(
                    {
                        "success": True,
                        "completed": True,
                        "redirect_url": reverse("taller:dashboard"),
                        "message": "¡Onboarding completado! Bienvenido a eGarage",
                    }
                )

    except Exception as e:
        return JsonResponse(
            {"success": False, "error": str(e), "message": "Error al guardar el paso"}
        )

    return JsonResponse({"success": False, "message": "Paso no válido"})


@login_required
@require_POST
def onboarding_agregar_tecnico(request):
    """
    Agrega un técnico durante el onboarding
    """
    try:
        empresa = get_active_empresa(request)
    except Exception:
        return JsonResponse({"success": False, "error": "Empresa no encontrada"})

    if not empresa:
        return JsonResponse({"success": False, "error": "Empresa no encontrada"})

    form = TecnicoForm(request.POST)
    if form.is_valid():
        tecnico = form.save(commit=False)
        tecnico.empresa = empresa
        tecnico.save()

        return JsonResponse(
            {
                "success": True,
                "tecnico": {
                    "id": tecnico.id,
                    "nombre": tecnico.nombre,
                    "especialidad": tecnico.especialidad or "General",
                },
                "message": "Técnico agregado correctamente",
            }
        )
    else:
        return JsonResponse(
            {"success": False, "errors": form.errors, "message": "Por favor corrige los errores"}
        )


@login_required
def onboarding_preview_documento(request):
    """
    Muestra una preview del encabezado de documento usando el partial real del PDF
    """
    try:
        empresa = get_active_empresa(request)
    except Exception:
        return JsonResponse({"success": False, "error": "Empresa no encontrada"})

    if not empresa:
        return JsonResponse({"success": False, "error": "Empresa no encontrada"})

    from django.template.loader import render_to_string

    # Datos simulados para el partial
    context = {
        "empresa": empresa,
        "company_name": empresa.nombre_taller,
        "logo_url": empresa.logo.url if empresa.logo else None,
        "company_address": empresa.direccion,
        "company_phone": empresa.telefono,
        "company_email": empresa.email,
        "company_website": getattr(empresa.config, "sitio_web", ""),
        "document_label": "PRESUPUESTO / QUOTE",
        "documento": {"numero_documento": "0001-TEST", "id": 1},
        "generated_at": timezone.now(),
        "cliente": {
            "nombre": "Cliente de Prueba",
            "tax_id": "12.345.678-9",
            "email": "cliente@ejemplo.com",
        },
        "vehiculo": "Toyota Hilux 2023 - [ABC-123]",
        "lineas_repuesto": [
            {
                "nombre": "Aceite de Motor 5W30",
                "cantidad": 4,
                "precio_unitario": 12000,
                "subtotal": 48000,
            },
            {
                "nombre": "Filtro de Aceite",
                "cantidad": 1,
                "precio_unitario": 8500,
                "subtotal": 8500,
            },
        ],
        "subtotal": 56500,
        "total": 56500 * 1.19 if empresa.pais == "CL" else 56500,
    }

    html_preview = render_to_string(
        "taller/documentos/pdf/documento_profesional_inner.html", context
    )

    accept = (request.headers.get("accept") or "").lower()
    wants_json = "application/json" in accept
    is_fetch = (request.headers.get("x-requested-with") or "").lower() == "xmlhttprequest"

    if not wants_json and not is_fetch:
        page = f"""<!doctype html>
<html lang=\"es\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Preview Documento</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;600;700&display=swap');
    :root {{
      --neon-cyan: #00ffff;
      --neon-purple: #b026ff;
      --neon-pink: #ff00ff;
      --dark-bg: #0a0e27;
      --text-primary: #ffffff;
      --text-secondary: #a0aec0;
    }}
    body {{
      margin: 0;
      font-family: 'Rajdhani', sans-serif;
      background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 50%, #0f1629 100%);
      background-attachment: fixed;
      color: var(--text-primary);
      min-height: 100vh;
      position: relative;
      overflow-x: hidden;
    }}
    body::before {{
      content: '';
      position: fixed;
      inset: 0;
      background-image:
        linear-gradient(rgba(0, 255, 255, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 255, 255, 0.03) 1px, transparent 1px);
      background-size: 50px 50px;
      pointer-events: none;
      z-index: 0;
    }}
    .wrap {{ max-width: 1100px; margin: 0 auto; padding: 20px 14px 28px; position: relative; z-index: 1; }}
    .header {{ display:flex; align-items:flex-end; justify-content:space-between; gap: 12px; margin: 6px 0 14px; flex-wrap: wrap; }}
    .title {{ font-size: 20px; font-weight: 900; font-family: 'Orbitron', sans-serif; letter-spacing: 1px; text-transform: uppercase; }}
    .subtitle {{ font-size: 13px; color: var(--text-secondary); margin-top: 4px; }}
    .chip {{ font-size: 12px; padding: 8px 10px; border: 1px solid rgba(0, 255, 255, 0.25); border-radius: 999px; background: rgba(21,25,50,.6); color: var(--text-secondary); backdrop-filter: blur(16px); }}
    .card {{ background: rgba(21,25,50,.7); border: 1px solid rgba(0,255,255,.2); border-radius: 16px; overflow: hidden; box-shadow: 0 8px 32px rgba(0,0,0,.3); backdrop-filter: blur(20px); }}
    .card-h {{ padding: 12px 14px; border-bottom: 1px solid rgba(0,255,255,.15); display:flex; align-items:center; justify-content:space-between; gap: 10px; }}
    .card-h strong {{ font-size: 12px; letter-spacing: .8px; text-transform: uppercase; color: var(--neon-cyan); }}
    .card-b {{ background: #ffffff; color: #0b1020; padding: 12px; }}
    .hint {{ font-size: 12px; color: var(--text-secondary); padding: 10px 2px 0; }}
    @media (max-width: 480px) {{
      .wrap {{ padding: 14px 12px 22px; }}
      .card-b {{ padding: 10px; }}
    }}
  </style>
</head>
<body>
  <div class=\"wrap\">
    <div class=\"header\">
      <div>
        <div class=\"title\">Preview de documento</div>
        <div class=\"subtitle\">Vista previa real del PDF (inner)</div>
      </div>
      <div class=\"chip\">{empresa.nombre_taller} · {empresa.get_pais_display()}</div>
    </div>

    <div class=\"card\">
      <div class=\"card-h\"><strong>Documento</strong><span class=\"chip\">/onboarding/preview-documento/</span></div>
      <div class=\"card-b\">{html_preview}</div>
    </div>

    <div class=\"hint\">Tip: esta URL devuelve JSON cuando se consume desde el onboarding. Abierta en navegador muestra esta página.</div>
  </div>
</body>
</html>"""
        return HttpResponse(page)

    return JsonResponse(
        {
            "success": True,
            "html": html_preview,
            "preview": {  # Mantener compatibilidad básica si se requiere
                "nombre_empresa": empresa.nombre_taller,
                "moneda": empresa.moneda,
            },
        }
    )
