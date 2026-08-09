from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.messages import get_messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import redirect, render
from django.contrib.auth.models import User

from taller.templatetags.role_tags import is_owner
from taller.context_processors import invalidate_company_cache
from taller.forms.company_settings_forms import (
    CompanyProfileForm,
    DominioPersonalizadoForm,
    FinancialSettingsForm,
    ThemeSettingsForm,
)
from taller.services.branding_service import BrandingService
from taller.models import Tecnico, TeamMember
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
    kept = []
    for message in get_messages(request):
        text = str(message)
        if any(fragment in text for fragment in NOISY_FLASH_FRAGMENTS):
            continue
        kept.append(message)
    for message in kept:
        messages.add_message(request, message.level, str(message), extra_tags=message.extra_tags)

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

def _subscription_price_context(empresa):
    country = (getattr(empresa, "pais", "") or "CL").upper()
    plan_code = normalize_plan_code(getattr(empresa, "plan", "") or PLAN_ENTRY)
    if plan_code == "trial":
        plan_code = PLAN_ENTRY
    monthly = get_plan_price(country, plan_code, BILLING_MONTHLY)
    annual = get_plan_price(country, plan_code, BILLING_ANNUAL)
    return {"monthly": monthly["price"], "annual": annual["price"], "currency": monthly["currency"]}

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
        if "crear_usuario_sistema" in request.POST:
            username = request.POST.get("username", "").strip()
            email = request.POST.get("email", "").strip()
            password = request.POST.get("password", "").strip()
            rol = request.POST.get("rol", "VENDEDOR").upper()

            if username and email and password:
                if User.objects.filter(username=username).exists():
                    messages.error(request, "El nombre de usuario ya está tomado.")
                elif User.objects.filter(email=email).exists():
                    messages.error(request, "El correo electrónico ya está registrado.")
                else:
                    user = User.objects.create_user(username=username, email=email, password=password)
                    TeamMember.objects.create(
                        user=user,
                        empresa=empresa,
                        rol=rol,
                        is_active=True,
                        creado_por=request.user
                    )
                    messages.success(request, f"Usuario '{username}' creado exitosamente con rol {rol}.")
            else:
                messages.error(request, "Todos los campos son requeridos.")
            return redirect(request.path)

        if "toggle_usuario_sistema" in request.POST:
            member_id = request.POST.get("toggle_usuario_sistema")
            try:
                member = TeamMember.objects.get(id=member_id, empresa=empresa)
                member.is_active = not member.is_active
                member.save()
                estado = "activado" if member.is_active else "desactivado"
                messages.success(request, f"Acceso del usuario '{member.user.username}' {estado} correctamente.")
            except TeamMember.DoesNotExist:
                messages.error(request, "Usuario no encontrado.")
            return redirect(request.path)

        if "registrar_dominio" in request.POST:
            form_dominio = DominioPersonalizadoForm(request.POST)
            if form_dominio.is_valid():
                try:
                    DomainService.registrar(empresa, form_dominio.cleaned_data["dominio"], creado_por=request.user)
                    messages.success(request, "Dominio registrado correctamente.")
                except ValidationError as exc:
                    for msg in exc.messages: messages.error(request, msg)
            return redirect(request.path)

        if "crear_tecnico" in request.POST:
            nombre = request.POST.get("nombre", "").strip() 
            if nombre:
                Tecnico.objects.create(empresa=empresa, nombre=nombre, activo=True)
                messages.success(request, f"Técnico '{nombre}' creado correctamente.")
            return redirect(request.path)

        if "toggle_tecnico" in request.POST:
            tecnico_id = request.POST.get("toggle_tecnico") 
            try:
                tecnico = Tecnico.objects.get(id=tecnico_id, empresa=empresa)
                tecnico.activo = not tecnico.activo
                tecnico.save()
                messages.success(request, f"Estado del técnico modificado.")
            except Tecnico.DoesNotExist: pass
            return redirect(request.path)

    tecnicos = Tecnico.objects.filter(empresa=empresa)
    usuarios_sistema = TeamMember.objects.filter(empresa=empresa).exclude(user=request.user).select_related('user')
    dominios = EmpresaDominio.objects.filter(empresa=empresa)

    return render(
        request,
        "taller/company/settings.html",
        {
            "config": config,
            "empresa": empresa,
            "config_empresa": config_empresa,
            "tecnicos": tecnicos,
            "usuarios_sistema": usuarios_sistema,
            "dominios": dominios,
            **_subscription_price_context(empresa),
        },
    )
