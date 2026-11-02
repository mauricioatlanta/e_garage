"""
BrandingService — Fuente única de verdad para la identidad visual de cada empresa.

Jerarquía de prioridad (menor a mayor, cada capa sobreescribe la anterior):
    Layer 3  Empresa           nombre_taller, pais, moneda, logo, contacto básico
    Layer 2  ConfiguracionEmpresa  nombre_publico, tagline, brand_color, rubro, contacto
    Layer 1  CompanySettings   company_name, primary/secondary_color, logo redimensionado

Si una capa no existe o falta un campo, el valor del nivel anterior persiste.

Uso típico:
    brand = BrandingService.get_brand(empresa, user=request.user)
    context.update(BrandingService.as_context(brand))
"""

import logging
from dataclasses import dataclass, field

from django.conf import settings as django_settings

logger = logging.getLogger(__name__)


@dataclass
class BrandData:
    """Snapshot de la identidad de marca de un tenant.

    Los templates acceden a este objeto como ``{{ BRAND.logo_url }}``,
    etc.  El método ``as_dict()`` provee un dict equivalente para
    compatibilidad con código que espera BRAND como dict.
    """

    name: str = "eGarage"
    tagline: str = ""
    logo_url: str = ""
    primary_color: str = "#0d6efd"
    secondary_color: str = "#6c757d"
    country: str = "cl"
    currency: str = "CLP"
    rubro: str = "WORKSHOP"
    secciones: dict = field(default_factory=dict)
    # Campos de contacto (usados por exportación PDF y Marketplace)
    address: str = ""
    phone: str = ""
    email: str = ""
    website: str = ""
    tax_id: str = ""

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "tagline": self.tagline,
            "logo_url": self.logo_url,
            "primary_color": self.primary_color,
            "secondary_color": self.secondary_color,
            "country": self.country,
            "currency": self.currency,
            "rubro": self.rubro,
            "secciones": self.secciones,
            "address": self.address,
            "phone": self.phone,
            "email": self.email,
            "website": self.website,
            "tax_id": self.tax_id,
        }


class BrandingService:
    """Resuelve la identidad visual de un tenant aplicando las tres capas en orden."""

    # ── API pública ────────────────────────────────────────────────────────────

    @classmethod
    def get_brand(cls, empresa, *, user=None) -> BrandData:
        """
        Devuelve la identidad de marca para *empresa*.

        :param empresa:  Instancia de Empresa.  None devuelve defaults del sistema.
        :param user:     Owner de la empresa.  Si se omite se infiere desde empresa.user.
        """
        brand = cls._defaults()

        if empresa is None:
            return brand

        if user is None:
            user = getattr(empresa, "user", None)

        # Orden de aplicación: Layer 3 → Layer 2 → Layer 1 (mayor prioridad gana)
        cls._apply_empresa(brand, empresa)
        cls._apply_configuracion_empresa(brand, empresa)
        if user is not None:
            cls._apply_company_settings(brand, user)

        return brand

    @classmethod
    def get_brand_for_request(cls, request) -> BrandData:
        """Atajo para context processors y vistas: resuelve empresa desde el request."""
        from django.contrib.auth.models import AnonymousUser

        empresa = getattr(request, "empresa", None) or getattr(request, "empresa_actual", None)
        user = getattr(request, "user", None)

        if user is None or isinstance(user, AnonymousUser) or not user.is_authenticated:
            user = None

        if empresa is None and user is not None:
            empresa = cls._get_empresa_from_user(user)

        return cls.get_brand(empresa, user=user)

    @classmethod
    def as_context(cls, brand: BrandData) -> dict:
        """
        Convierte un BrandData al dict de contexto que los templates esperan.

        Incluye el objeto ``BRAND`` y los alias legacy que usan los templates
        existentes (``company_name``, ``primary_color``, etc.).
        """
        d = brand.as_dict()
        return {
            "BRAND": d,
            # Aliases legacy — mantener para no romper templates existentes
            "company_name": d["name"],
            "company_logo_url": d["logo_url"],
            "company_tagline": d["tagline"],
            "primary_color": d["primary_color"],
            "secondary_color": d["secondary_color"],
            "company_color": d["primary_color"],
            "company_country": d["country"],
            "company_currency": d["currency"],
        }

    @classmethod
    def sync_to_legacy_models(cls, company_settings, config_empresa, empresa) -> None:
        """
        Propaga cambios de CompanySettings → ConfiguracionEmpresa y Empresa.

        Reemplaza la función ``_sync_company_models`` de company_settings_views.
        Solo guarda los campos que realmente cambiaron (update_fields).
        """
        from django.db import IntegrityError

        from taller.models.empresa import Empresa as EmpresaModel

        empresa_updates = []
        config_updates = []

        # ── Empresa ──────────────────────────────────────────────────────────
        if empresa.nombre_taller != company_settings.company_name:
            empresa.nombre_taller = company_settings.company_name
            empresa_updates.append("nombre_taller")

        if empresa.direccion != company_settings.address:
            empresa.direccion = company_settings.address
            empresa_updates.append("direccion")

        if empresa.email != company_settings.email:
            empresa.email = company_settings.email
            empresa_updates.append("email")

        if empresa.telefono != company_settings.phone:
            phone_taken = bool(
                company_settings.phone
                and EmpresaModel.objects.filter(telefono=company_settings.phone)
                .exclude(pk=empresa.pk)
                .exists()
            )
            if not phone_taken:
                empresa.telefono = company_settings.phone
                empresa_updates.append("telefono")

        if company_settings.logo:
            logo_name = company_settings.logo.name
            if getattr(empresa.logo, "name", "") != logo_name:
                empresa.logo = logo_name
                empresa_updates.append("logo")

        # ── ConfiguracionEmpresa ──────────────────────────────────────────────
        _conf_mapping = [
            ("nombre_publico",             "company_name"),
            ("tagline",                    "tagline"),
            ("direccion",                  "address"),
            ("telefono",                   "phone"),
            ("email_contacto",             "email"),
            ("sitio_web",                  "website"),
            ("moneda",                     "currency"),
            ("tasa_impuesto",              "tax_rate"),
            ("sales_tax_rate",             "tax_rate"),
            ("aplicar_impuesto_por_defecto", "apply_tax_by_default"),
            ("dividir_por_tecnico",        "separate_by_technician"),
            ("brand_color",                "primary_color"),
        ]
        for conf_field, settings_field in _conf_mapping:
            conf_val = getattr(config_empresa, conf_field, None)
            settings_val = getattr(company_settings, settings_field, None)
            if conf_val != settings_val:
                setattr(config_empresa, conf_field, settings_val)
                config_updates.append(conf_field)

        if company_settings.logo:
            logo_name = company_settings.logo.name
            if getattr(config_empresa.logo, "name", "") != logo_name:
                config_empresa.logo = logo_name
                config_updates.append("logo")

        # ── Guardar ──────────────────────────────────────────────────────────
        if empresa_updates:
            try:
                empresa.save(update_fields=empresa_updates)
            except IntegrityError:
                safe = [f for f in empresa_updates if f != "telefono"]
                if safe:
                    empresa.save(update_fields=safe)

        if config_updates:
            config_empresa.save(update_fields=config_updates)

    # ── Helpers privados ───────────────────────────────────────────────────────

    @classmethod
    def _defaults(cls) -> BrandData:
        return BrandData(
            name=getattr(django_settings, "DEFAULT_BRAND_NAME", "eGarage"),
            tagline=getattr(django_settings, "DEFAULT_BRAND_TAGLINE", "Control total para tu taller"),
            logo_url=getattr(django_settings, "DEFAULT_BRAND_LOGO_URL", "") or "",
            primary_color=getattr(django_settings, "DEFAULT_BRAND_PRIMARY_COLOR", "#0d6efd"),
            secondary_color=getattr(django_settings, "DEFAULT_BRAND_SECONDARY_COLOR", "#6c757d"),
            country=getattr(django_settings, "DEFAULT_BRAND_COUNTRY", "cl"),
            currency=getattr(django_settings, "DEFAULT_BRAND_CURRENCY", "CLP"),
        )

    @classmethod
    def _apply_empresa(cls, brand: BrandData, empresa) -> None:
        """Layer 3 — campos directos en Empresa."""
        if getattr(empresa, "nombre_taller", None):
            brand.name = empresa.nombre_taller
        if getattr(empresa, "pais", None):
            brand.country = empresa.pais.lower()
        if getattr(empresa, "moneda", None):
            brand.currency = empresa.moneda

        logo = getattr(empresa, "logo", None)
        if logo:
            try:
                brand.logo_url = logo.url
            except Exception:
                pass

        for attr in ("tagline", "lema"):
            val = getattr(empresa, attr, None)
            if val:
                brand.tagline = val
                break

        for attr in ("direccion", "address"):
            val = getattr(empresa, attr, None)
            if val:
                brand.address = val
                break

        if getattr(empresa, "telefono", None):
            brand.phone = empresa.telefono
        if getattr(empresa, "email", None):
            brand.email = empresa.email

    @classmethod
    def _apply_configuracion_empresa(cls, brand: BrandData, empresa) -> None:
        """Layer 2 — ConfiguracionEmpresa."""
        try:
            from taller.models.configuracion import ConfiguracionEmpresa
            conf = ConfiguracionEmpresa.objects.get(empresa=empresa)
        except Exception:
            return

        if getattr(conf, "nombre_publico", None):
            brand.name = conf.nombre_publico
        for attr in ("tagline", "lema"):
            val = getattr(conf, attr, None)
            if val:
                brand.tagline = val
                break

        logo = getattr(conf, "logo", None)
        if logo:
            try:
                brand.logo_url = logo.url
            except Exception:
                pass

        if getattr(conf, "brand_color", None):
            brand.primary_color = conf.brand_color
        if getattr(conf, "moneda", None):
            brand.currency = conf.moneda
        if getattr(conf, "pais", None):
            brand.country = conf.pais.lower()

        brand.rubro = getattr(conf, "rubro_principal", None) or "WORKSHOP"
        try:
            brand.secciones = conf.get_secciones_visibles()
        except Exception:
            pass

        if getattr(conf, "direccion", None):
            brand.address = conf.direccion
        if getattr(conf, "telefono", None):
            brand.phone = conf.telefono
        if getattr(conf, "email_contacto", None):
            brand.email = conf.email_contacto
        if getattr(conf, "sitio_web", None):
            brand.website = conf.sitio_web

    @classmethod
    def _apply_company_settings(cls, brand: BrandData, user) -> None:
        """Layer 1 (más alta prioridad) — CompanySettings."""
        try:
            from taller.models.company_settings import CompanySettings
            cs = CompanySettings.objects.get(user=user)
        except Exception:
            return

        if cs.company_name:
            brand.name = cs.company_name
        if getattr(cs, "tagline", None):
            brand.tagline = cs.tagline

        logo = getattr(cs, "logo", None)
        if logo:
            try:
                brand.logo_url = logo.url
            except Exception:
                pass

        if getattr(cs, "primary_color", None):
            brand.primary_color = cs.primary_color
        if getattr(cs, "secondary_color", None):
            brand.secondary_color = cs.secondary_color
        if getattr(cs, "currency", None):
            brand.currency = cs.currency

        if getattr(cs, "address", None):
            brand.address = cs.address
        if getattr(cs, "phone", None):
            brand.phone = cs.phone
        if getattr(cs, "email", None):
            brand.email = cs.email
        if getattr(cs, "website", None):
            brand.website = cs.website
        if getattr(cs, "tax_id", None):
            brand.tax_id = cs.tax_id

    @classmethod
    def _get_empresa_from_user(cls, user):
        """Obtiene la empresa de un usuario (DB lookup — solo cuando el middleware no corrió)."""
        try:
            from taller.models.empresa import Empresa
            return Empresa.objects.get(user=user)
        except Exception:
            return None
