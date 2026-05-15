"""
Models package para taller
"""

# Importar modelos principales para compatibilidad con importaciones desde taller.models
# Estos son los modelos más usados en el código base

# Modelos básicos (sin dependencias circulares)
from .empresa import Empresa
from .tecnico import Tecnico
from .configuracion import ConfiguracionEmpresa
from .team_member import TeamMember

# Modelos de clientes y vehículos
from .clientes import Cliente
from .vehiculos import Vehiculo

# Modelos de documentos
from .documento import Documento
from .lineas_documento import LineaServicio, LineaRepuesto, LineaOtroServicio

# Modelos de repuestos
from .repuesto import Repuesto

# Modelos de ubicación
from .ubicacion import Estado, Ciudad

# Modelos de suscripción y pagos
from .comprobante_pago import ComprobantePago
from .trial import TrialRegistro

__all__ = [
    # Modelos básicos
    "Empresa",
    "Tecnico",
    "ConfiguracionEmpresa",
    "TeamMember",
    # Clientes y vehículos
    "Cliente",
    "Vehiculo",
    # Documentos
    "Documento",
    "LineaServicio",
    "LineaRepuesto",
    "LineaOtroServicio",
    # Repuestos
    "Repuesto",
    # Ubicación
    "Estado",
    "Ciudad",
    # Suscripción y pagos
    "ComprobantePago",
    "TrialRegistro",
]

# Intentar importar otros modelos si existen (para compatibilidad)
try:
    from .company_settings import CompanySettings, CompanySettingsHistory

    __all__.extend(["CompanySettings", "CompanySettingsHistory"])
except ImportError:
    pass

# Intentar importar modelos de catálogo si existen
try:
    from .catalogo_repuestos import TaxPolicy, Part, PartI18N, PartPrice
    from .catalogo_servicios import Service, ServiceI18N, ServicePrice

    __all__.extend(
        ["TaxPolicy", "Part", "PartI18N", "PartPrice", "Service", "ServiceI18N", "ServicePrice"]
    )
except ImportError:
    pass
