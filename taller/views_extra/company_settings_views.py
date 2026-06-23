from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.messages import get_messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render

from taller.templatetags.role_tags import is_owner

from taller.context_processors import invalidate_company_cache
from taller.forms.company_settings_forms import (
    CompanyProfileForm,
    FinancialSettingsForm,
    ThemeSettingsForm,
)
from taller.models import Tecnico
from taller.models.company_settings import CompanySettings
from taller.models.configuracion import ConfiguracionEmpresa
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
    empresa_updates = []
    config_updates = []

    if empresa.nombre_taller != config.company_name:
        empresa.nombre_taller = config.company_name
        empresa_updates.append("nombre_taller")
    if empresa.direccion != config.address:
        empresa.direccion = config.address
        empresa_updates.append("direccion")
    if empresa.telefono != config.phone:
        from taller.models.empresa import Empresa as EmpresaModel
        phone_taken = (
            config.phone
            and EmpresaModel.objects.filter(telefono=config.phone)
            .exclude(pk=empresa.pk)
            .exists()
        )
        if not phone_taken:
            empresa.telefono = config.phone
            empresa_updates.append("telefono")
    if empresa.email != config.email:
        empresa.email = config.email
        empresa_updates.append("email")
    if config.logo:
        logo_name = config.logo.name
        if getattr(empresa.logo, "name", "") != logo_name:
            empresa.logo = logo_name
            empresa_updates.append("logo")

    if config_empresa.nombre_publico != config.company_name:
        config_empresa.nombre_publico = config.company_name
        config_updates.append("nombre_publico")
    if config_empresa.tagline != config.tagline:
        config_empresa.tagline = config.tagline
        config_updates.append("tagline")
    if config_empresa.direccion != config.address:
        config_empresa.direccion = config.address
        config_updates.append("direccion")
    if config_empresa.telefono != config.phone:
        config_empresa.telefono = config.phone
        config_updates.append("telefono")
    if config_empresa.email_contacto != config.email:
        config_empresa.email_contacto = config.email
        config_updates.append("email_contacto")
    if config_empresa.sitio_web != config.website:
        config_empresa.sitio_web = config.website
        config_updates.append("sitio_web")
    if config_empresa.moneda != config.currency:
        config_empresa.moneda = config.currency
        config_updates.append("moneda")
    if config_empresa.tasa_impuesto != config.tax_rate:
        config_empresa.tasa_impuesto = config.tax_rate
        config_updates.append("tasa_impuesto")
    if config_empresa.sales_tax_rate != config.tax_rate:
        config_empresa.sales_tax_rate = config.tax_rate
        config_updates.append("sales_tax_rate")
    if config_empresa.aplicar_impuesto_por_defecto != config.apply_tax_by_default:
        config_empresa.aplicar_impuesto_por_defecto = config.apply_tax_by_default
        config_updates.append("aplicar_impuesto_por_defecto")
    if config_empresa.dividir_por_tecnico != config.separate_by_technician:
        config_empresa.dividir_por_tecnico = config.separate_by_technician
        config_updates.append("dividir_por_tecnico")
    if config_empresa.brand_color != config.primary_color:
        config_empresa.brand_color = config.primary_color
        config_updates.append("brand_color")
    if config.logo:
        logo_name = config.logo.name
        if getattr(config_empresa.logo, "name", "") != logo_name:
            config_empresa.logo = logo_name
            config_updates.append("logo")

    if empresa_updates:
        from django.db import IntegrityError
        try:
            empresa.save(update_fields=empresa_updates)
        except IntegrityError:
            # Constraint en empresa — guarda sin telefono como fallback
            safe = [f for f in empresa_updates if f != "telefono"]
            if safe:
                empresa.save(update_fields=safe)
    if config_updates:
        config_empresa.save(update_fields=config_updates)


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
