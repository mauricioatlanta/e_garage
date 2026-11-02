from decimal import Decimal

from taller.models.configuracion import ConfiguracionEmpresa
from taller.utils.country_config import get_country_config


class CompanyDefaultsService:
    @staticmethod
    def apply_defaults_to_empresa(empresa, *, country_code=None, commit=True):
        if empresa is None:
            return None

        if country_code:
            empresa.pais = (country_code or "CL").upper()
        else:
            empresa.pais = (getattr(empresa, "pais", None) or "CL").upper()

        config = get_country_config(empresa.pais)

        changed_fields = set()

        moneda = getattr(empresa, "moneda", None)
        if not moneda:
            empresa.moneda = config.get("currency")
            changed_fields.add("moneda")

        zona_horaria = getattr(empresa, "zona_horaria", None)
        if not zona_horaria:
            empresa.zona_horaria = config.get("timezone")
            changed_fields.add("zona_horaria")

        if commit and changed_fields:
            empresa.save(update_fields=list(changed_fields))

        return empresa

    @staticmethod
    def get_or_create_configuracion_empresa(empresa):
        if not empresa:
            return None
        config, _ = ConfiguracionEmpresa.objects.get_or_create(empresa=empresa)
        return config

    @staticmethod
    def apply_defaults_to_configuracion(configuracion, *, empresa=None, commit=True):
        if configuracion is None and empresa is not None:
            configuracion = CompanyDefaultsService.get_or_create_configuracion_empresa(empresa)

        if configuracion is None:
            return None

        if empresa is None:
            empresa = getattr(configuracion, "empresa", None)

        country_code = (getattr(empresa, "pais", None) or "CL").upper()
        country_config = get_country_config(country_code)

        changed_fields = set()

        moneda = getattr(configuracion, "moneda", None)
        if not moneda:
            configuracion.moneda = country_config.get("currency")
            changed_fields.add("moneda")

        tasa_impuesto = getattr(configuracion, "tasa_impuesto", None)
        if tasa_impuesto in (None, ""):
            configuracion.tasa_impuesto = Decimal(str(country_config.get("tax_rate", 0.0)))
            changed_fields.add("tasa_impuesto")

        aplicar_impuesto = getattr(configuracion, "aplicar_impuesto_por_defecto", None)
        if aplicar_impuesto is None:
            configuracion.aplicar_impuesto_por_defecto = bool(country_config.get("tax_rate", 0.0))
            changed_fields.add("aplicar_impuesto_por_defecto")

        if commit and changed_fields:
            configuracion.save(update_fields=list(changed_fields))

        return configuracion
