from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.messages import get_messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import redirect, render

from taller.templatetags.role_tags import is_owner

from taller.context_processors import invalidate_company_cache
from taller.forms.company_settings_forms import (
    CompanyProfileForm,
    DominioPersonalizadoForm,
    FinancialSettingsForm,
    ThemeSettingsForm,
)
from taller.services.branding_service import BrandingService
from taller.models import Tecnico
from taller.models.company_settings import CompanySettings
from taller.models.configuracion import ConfiguracionEmpresa
from taller.models.empresa_dominio import EmpresaDominio
from taller.services.domain_service import DomainService
from taller.utils.country_config import get_country_config
from taller.utils.empresa import get_or_create_empresa
from taller.utils.payment_config import get_transfer_payment_details
from taller.utils.plan_catalog import (
    BILLING_ANNUAL,
    BILLING_MONTHLY,
    PLAN_ENTRY,
    get_plan_price,
    normalize_plan_code,
)


SPANISH_COUNTRIES = {"CL", "MX", "PE", "VE", "CO", "EC", "AR", "UY", "BR"}

NOISY_FLASH_FRAGMENTS = (
    "Ha iniciado sesión exitosamente",
    "Successfully signed in",
    "Selecciona o crea tu empresa para continuar",
    "Usuario sin empresa asignada",
    "Usuario sin empresa asociada",
)


def _discard_noisy_flash_messages(request):
    """Limpia avisos internos acumulados sin borrar mensajes útiles de settings."""
    kept = []
    for message in get_messages(request):
        text = str(message)
        if any(fragment in text for fragment in NOISY_FLASH_FRAGMENTS):
            continue
        kept.append(message)

    for message in kept:
        messages.add_message(
            request,
            message.level,
            str(message),
            extra_tags=message.extra_tags,
        )


def _get_or_create_company_settings(user, empresa):
    try:
        return CompanySettings.objects.get(user=user)
    except CompanySettings.DoesNotExist:
        country_config = get_country_config(getattr(empresa, "pais", "CL"))
        return CompanySettings.objects.create(
            user=user,
            company_name=empresa.nombre_taller or "Mi Empresa",
            tagline="",
            primary_color="#0d6efd",
            secondary_color="#6c757d",
            currency=country_config.get("currency", "CLP"),
            timezone=country_config.get("timezone", "America/Santiago"),
            tax_rate=Decimal(str(country_config.get("tax_rate", 0.0))),
            apply_tax_by_default=bool(country_config.get("tax_rate", 0.0)),
        )


def _collect_form_errors(forms):
    errors = []
    for form in forms:
        for field_name, field_errors in form.errors.items():
            label = form.fields.get(field_name).label if field_name in form.fields else field_name
            for error in field_errors:
                errors.append(f"{label or field_name}: {error}")
    return errors


def _sync_company_models(config, config_empresa, empresa):
    """Wrapper de compatibilidad — delega a BrandingService.sync_to_legacy_models."""
    BrandingService.sync_to_legacy_models(config, config_empresa, empresa)


def _subscription_price_context(empresa):
    country = (getattr(empresa, "pais", "") or "CL").upper()
    plan_code = normalize_plan_code(getattr(empresa, "plan", "") or PLAN_ENTRY)
    if plan_code == "trial":
        plan_code = PLAN_ENTRY

    monthly = get_plan_price(country, plan_code, BILLING_MONTHLY)
    annual = get_plan_price(country, plan_code, BILLING_ANNUAL)
    return {
        "monthly": monthly["price"],
        "annual": annual["price"],
        "currency": monthly["currency"],
    }


@login_required(login_url=None)
def company_settings_view(request):
    if not is_owner(request.user):
        raise PermissionDenied("Solo el dueño puede acceder a la configuración.")
    empresa = get_or_create_empresa(request)
    if request.method == "GET":
        _discard_noisy_flash_messages(request)

    config_empresa, _ = ConfiguracionEmpresa.objects.get_or_create(
        empresa=empresa,
        defaults={"sales_tax_rate": Decimal("19.00"), "tasa_impuesto": Decimal("19.00")},
    )
    config = _get_or_create_company_settings(request.user, empresa)
    is_spanish = getattr(empresa, "pais", "CL") in SPANISH_COUNTRIES

    if request.method == "POST":
        if "registrar_dominio" in request.POST:
            form_dominio = DominioPersonalizadoForm(request.POST)
            if form_dominio.is_valid():
                try:
                    DomainService.registrar(
                        empresa,
                        form_dominio.cleaned_data["dominio"],
                        creado_por=request.user,
                    )
                    messages.success(
                        request,
                        "Dominio registrado. Configura los registros DNS para verificarlo.",
                    )
                except ValidationError as exc:
                    for msg in exc.messages:
                        messages.error(request, msg)
            else:
                for errs in form_dominio.errors.values():
                    for err in errs:
                        messages.error(request, err)
            return redirect(request.path)

        if "solicitar_verificacion" in request.POST:
            dominio_id = request.POST.get("solicitar_verificacion")
            try:
                ed = EmpresaDominio.objects.get(pk=dominio_id, empresa=empresa)
                DomainService.preparar_verificacion(ed)
                messages.success(
                    request,
                    f"Verificación iniciada para {ed.dominio}. "
                    "Revisaremos tus registros DNS en breve.",
                )
            except EmpresaDominio.DoesNotExist:
                messages.error(request, "Dominio no encontrado.")
            except ValueError as exc:
                messages.error(request, str(exc))
            return redirect(request.path)

        if "crear_tecnico" in request.POST:
            nombre = request.POST.get("nombre", "").strip()
            telefono = request.POST.get("telefono", "").strip()
            direccion = request.POST.get("direccion", "").strip()

            if nombre:
                try:
                    Tecnico.objects.create(
                        nombre=nombre,
                        telefono=telefono or None,
                        direccion=direccion or None,
                        empresa=empresa,
                        activo=True,
                    )
                    if is_spanish:
                        messages.success(request, f"Técnico '{nombre}' creado correctamente.")
                    else:
                        messages.success(request, f"Technician '{nombre}' created successfully.")
                except Exception as exc:
                    if is_spanish:
                        messages.error(request, f"Error al crear técnico: {exc}")
                    else:
                        messages.error(request, f"Error creating technician: {exc}")
            else:
                if is_spanish:
                    messages.error(request, "El nombre es obligatorio.")
                else:
                    messages.error(request, "Name is required.")

            return redirect(request.path)

        if "toggle_tecnico" in request.POST:
            tecnico_id = request.POST.get("toggle_tecnico")

            try:
                tecnico = Tecnico.objects.get(id=tecnico_id, empresa=empresa)
                tecnico.activo = not tecnico.activo
                tecnico.save(update_fields=["activo", "fecha_modificacion"])

                if is_spanish:
                    estado = "activado" if tecnico.activo else "desactivado"
                    messages.success(request, f"Técnico '{tecnico.nombre}' {estado} correctamente.")
                else:
                    estado = "activated" if tecnico.activo else "deactivated"
                    messages.success(
                        request,
                        f"Technician '{tecnico.nombre}' {estado} successfully.",
                    )
            except Tecnico.DoesNotExist:
                if is_spanish:
                    messages.error(request, "Técnico no encontrado.")
                else:
                    messages.error(request, "Technician not found.")

            return redirect(request.path)

        post_data = request.POST.copy()

        # Chile: IVA 19% por defecto. No bloquear guardado si el input no llega por estar en otra pesta?a.
        if not post_data.get("tax_rate"):
            post_data["tax_rate"] = "19.00"

        if "apply_tax_by_default" not in post_data:
            post_data["apply_tax_by_default"] = "on"

        profile_form = CompanyProfileForm(post_data, request.FILES, instance=config)
        financial_form = FinancialSettingsForm(post_data, instance=config)
        theme_form = ThemeSettingsForm(post_data, instance=config)
        forms = [profile_form, financial_form, theme_form]

        forms_are_valid = True
        for form in forms:
            forms_are_valid = form.is_valid() and forms_are_valid

        if forms_are_valid:
            for form in forms:
                for field_name in form.fields:
                    if field_name in form.cleaned_data:
                        setattr(config, field_name, form.cleaned_data[field_name])

            config.save()

            # REFRESH REAL DESDE DB
            config.refresh_from_db()
            config_empresa.refresh_from_db()

            _sync_company_models(config, config_empresa, empresa)

            # REFRESH POST SYNC
            config.refresh_from_db()
            config_empresa.refresh_from_db()

            invalidate_company_cache(request.user)

            if is_spanish:
                messages.success(request, "Configuración guardada correctamente.")
            else:
                messages.success(request, "Settings saved successfully.")

            return redirect(request.path)

        error_messages = _collect_form_errors(forms)
        if is_spanish:
            messages.error(
                request,
                "Revise los campos del formulario: " + "; ".join(error_messages),
            )
        else:
            messages.error(
                request,
                "Please review the form fields: " + "; ".join(error_messages),
            )

    tecnicos = Tecnico.objects.filter(empresa=empresa).order_by("nombre")
    dominios = DomainService.listar_para_empresa(empresa)
    dominio_activo = DomainService.get_activo_para_empresa(empresa)
    form_dominio = DominioPersonalizadoForm()

    # SUBSCRIPTION CONTEXT
    subscription = None
    subscription_is_active = False
    subscription_status = "inactive"

    try:
        from taller.models.suscripcion import Suscripcion

        subscription = (
            Suscripcion.objects
            .filter(user=request.user)
            .first()
        )

        if subscription:
            subscription_is_active = bool(subscription.activa)

            if subscription.esta_vencida():
                subscription_status = "expired"
            elif subscription.activa:
                subscription_status = "active"
            else:
                subscription_status = "inactive"

    except Exception as exc:
        print(f"[SUBSCRIPTION CONTEXT ERROR] {exc}")


    # UI SUBSCRIPTION DERIVED STATE
    # Fallback: usa empresa.plan si no hay Suscripcion o si es trial
    empresa_plan = getattr(empresa, "plan", "trial") or "trial"
    empresa_estado_suscripcion = "inactiva"
    empresa_dias_restantes = 0
    empresa_fecha_vencimiento = None
    empresa_color_estado = "#dc3545"

    if subscription:
        suscripcion_tipo = getattr(subscription, "tipo", None)
        # Suscripcion.tipo usa códigos legacy distintos; solo lo usa si no es trial o si empresa.plan es trial
        if suscripcion_tipo and suscripcion_tipo != "trial":
            empresa_plan = suscripcion_tipo
        # Si empresa.plan es más específico (pro/taller/express), prevalece sobre el tipo legacy
        empresa_plan_directo = getattr(empresa, "plan", None)
        if empresa_plan_directo and empresa_plan_directo not in ("trial",):
            empresa_plan = empresa_plan_directo

        empresa_fecha_vencimiento = getattr(
            subscription,
            "fecha_fin",
            None
        )

        if subscription.esta_vencida():
            empresa_estado_suscripcion = "vencida"
            empresa_color_estado = "#dc3545"

        elif subscription.por_vencer():
            empresa_estado_suscripcion = "advertencia"
            empresa_color_estado = "#ffc107"

        elif getattr(subscription, "activa", False):
            empresa_estado_suscripcion = "activa"
            empresa_color_estado = "#198754"

        if empresa_fecha_vencimiento:
            from django.utils import timezone

            empresa_dias_restantes = max(
                0,
                (
                    empresa_fecha_vencimiento
                    - timezone.now().date()
                ).days
            )


    return render(
        request,
        "taller/company/settings.html",
        {
            "empresa": empresa,
            "tecnicos": tecnicos,
            "config": config,
            "config_empresa": config_empresa,
            "datos_transferencia": get_transfer_payment_details(empresa.pais),
            "subscription_prices": _subscription_price_context(empresa),
            "dominios": dominios,
            "dominio_activo": dominio_activo,
            "form_dominio": form_dominio,

            # SUBSCRIPTION
            "subscription": subscription,
            "subscription_is_active": subscription_is_active,
            "subscription_status": subscription_status,

            # UI DERIVED SUBSCRIPTION
            "empresa_plan": empresa_plan,
            "empresa_estado_suscripcion": empresa_estado_suscripcion,
            "empresa_dias_restantes": empresa_dias_restantes,
            "empresa_fecha_vencimiento": empresa_fecha_vencimiento,
            "empresa_color_estado": empresa_color_estado,
        },
    )
