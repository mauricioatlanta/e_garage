import re

from django.core.exceptions import ValidationError
from django.utils import timezone

from taller.models.configuracion import ConfiguracionEmpresa
from taller.models.tecnico import Tecnico

PHONE_RE = re.compile(r"^[\d\s\-\+\(\)]+$")


class OnboardingService:
    """Reglas server-side para onboarding obligatorio de empresas nuevas."""

    STEP_NAMES = {
        1: "identidad",
        2: "equipo",
        3: "finalizar",
    }
    STEP_NUMBERS = {v: k for k, v in STEP_NAMES.items()}

    @staticmethod
    def normalize_step(step):
        if step is None:
            return None
        if isinstance(step, int):
            return step if step in OnboardingService.STEP_NAMES else None
        return OnboardingService.STEP_NUMBERS.get(str(step).strip().lower())

    @staticmethod
    def is_valid_phone(value):
        phone = (value or "").strip()
        return len(phone) >= 8 and bool(PHONE_RE.match(phone))

    @staticmethod
    def validate_tecnico_data(nombre, telefono):
        errors = {}
        nombre = (nombre or "").strip()
        telefono = (telefono or "").strip()
        if len(nombre) < 2:
            errors["nombre"] = "El nombre del técnico debe tener al menos 2 caracteres."
        if not OnboardingService.is_valid_phone(telefono):
            errors["telefono"] = (
                "El teléfono es obligatorio y debe tener al menos 8 caracteres. "
                "Solo números, espacios, guiones, + y paréntesis."
            )
        if errors:
            raise ValidationError(errors)

    @staticmethod
    def is_placeholder_business_name(empresa, user=None):
        name = (getattr(empresa, "nombre_taller", "") or "").strip()
        if len(name) < 3:
            return True

        normalized = " ".join(name.lower().split())
        generic = {
            "mi taller",
            "taller",
            "mi empresa",
            "empresa",
            "sin nombre",
        }
        if normalized in generic:
            return True

        generated_placeholder = OnboardingService.generated_placeholder_name(user)
        if generated_placeholder and normalized == generated_placeholder:
            return True

        return False

    @staticmethod
    def generated_placeholder_name(user):
        if user is None:
            return ""
        source = (
            getattr(user, "first_name", None)
            or getattr(user, "username", None)
            or getattr(user, "email", None)
            or ""
        )
        source = str(source).strip()
        if not source:
            return ""
        return " ".join(f"Taller de {source}".lower().split())

    @staticmethod
    def get_config(empresa):
        if empresa is None:
            return None
        return ConfiguracionEmpresa.objects.filter(empresa=empresa).first()

    @staticmethod
    def has_identity(empresa, user=None):
        if empresa is None or OnboardingService.is_placeholder_business_name(empresa, user=user):
            return False
        config = OnboardingService.get_config(empresa)
        if config is None or not getattr(config, "rubro_principal", None):
            return False
        if not OnboardingService.is_valid_phone(getattr(empresa, "telefono", "")):
            return False
        if not (getattr(empresa, "email", "") or "").strip():
            return False
        if not (getattr(empresa, "direccion", "") or "").strip():
            return False
        return True

    @staticmethod
    def has_operational_team(empresa):
        if empresa is None:
            return False
        tecnicos = Tecnico.objects.filter(
            empresa=empresa,
            activo=True,
            nombre__isnull=False,
            telefono__isnull=False,
        ).exclude(nombre="").exclude(telefono="").exists()
        if not tecnicos:
            return False
        for tecnico in Tecnico.objects.filter(empresa=empresa, activo=True):
            if (
                len((tecnico.nombre or "").strip()) >= 2
                and OnboardingService.is_valid_phone(tecnico.telefono)
                and (tecnico.rol or "").strip()
            ):
                return True
        return False

    @staticmethod
    def validation_status(empresa, user=None):
        checks = {
            "identidad": OnboardingService.has_identity(empresa, user=user),
            "equipo": OnboardingService.has_operational_team(empresa),
        }
        return {
            "checks": checks,
            "complete": all(checks.values()),
        }

    @staticmethod
    def assert_can_complete(empresa, user=None):
        status = OnboardingService.validation_status(empresa, user=user)
        if status["complete"]:
            return status
        missing = [key for key, ok in status["checks"].items() if not ok]
        raise ValidationError(
            "No puedes finalizar el onboarding hasta completar: " + ", ".join(missing)
        )

    @staticmethod
    def mark_started(empresa):
        if empresa and not getattr(empresa, "onboarding_started_at", None):
            empresa.onboarding_started_at = timezone.now()
            empresa.save(update_fields=["onboarding_started_at"])

    @staticmethod
    def mark_completed(empresa):
        empresa.onboarding_completado = True
        empresa.onboarding_completed_at = timezone.now()
        empresa.onboarding_step = 3
        empresa.save(
            update_fields=[
                "onboarding_completado",
                "onboarding_completed_at",
                "onboarding_step",
            ]
        )
        return empresa


def country_prefix_for_request(request, empresa=None):
    path = (getattr(request, "path", "") or "").lower()
    parts = [p for p in path.split("/") if p]
    if len(parts) >= 2 and len(parts[0]) == 2 and len(parts[1]) == 2:
        return f"/{parts[0]}/{parts[1]}"

    country = (getattr(empresa, "pais", None) or "").upper()
    if country == "US":
        return "/us/en"
    if country == "CL":
        return "/cl/es"
    if country:
        return f"/{country.lower()}/es"
    return "/cl/es"


def language_code_for_request(request, empresa=None):
    path = (getattr(request, "path", "") or "").lower()
    parts = [p for p in path.split("/") if p]
    if len(parts) >= 2 and len(parts[0]) == 2 and len(parts[1]) == 2:
        return parts[1]

    country = (getattr(empresa, "pais", None) or "").upper()
    if country == "US":
        return "en"
    if country == "BR":
        return "pt"
    return "es"


def onboarding_step_url(request, empresa, step):
    step_num = OnboardingService.normalize_step(step) or 1
    return f"{country_prefix_for_request(request, empresa)}/onboarding/{OnboardingService.STEP_NAMES[step_num]}/"


def workspace_url(request, empresa):
    return f"{country_prefix_for_request(request, empresa)}/workspace/"
