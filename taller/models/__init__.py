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
from .marca import Marca

# Modelos de kilometraje
from .kilometraje import KilometrajeRegistro
from .registro_kilometraje import RegistroKilometraje
from .checklist_ingreso import ChecklistIngreso

# Modelos de documentos
from .documento import Documento
from .lineas_documento import LineaServicio, LineaRepuesto, LineaOtroServicio

# Modelos de memoria y seguimiento
from .memoria_seguimiento import (
    NotaInterna,
    EtiquetaInterna,
    EtiquetaAsignacion,
    EvidenciaDocumento,
    SeguimientoPublico,
)

# Modelos de repuestos
from .repuesto import Repuesto

# Modelos de ubicación
from .ubicacion import Estado, Ciudad

# Modelos de suscripción y pagos
from .comprobante_pago import ComprobantePago
from .trial import TrialRegistro

# Modelos legacy / compatibilidad (import opcional por si faltan en algún deploy)
from .auditoria import LogAuditoria

try:
    from .pago import PagoPendiente
except ImportError:
    PagoPendiente = None
try:
    from .regimen_fiscal import RegimenFiscal
except ImportError:
    RegimenFiscal = None
try:
    from .marcas_usa import MarcaVehiculo, ModeloVehiculo
except ImportError:
    MarcaVehiculo = ModeloVehiculo = None

# Modelos de extras de vehículos
from .extras_vehiculo import CajaVehiculo, ColorVehiculo, MotorVehiculo

__all__ = [
    # Modelos básicos
    "Empresa",
    "Tecnico",
    "ConfiguracionEmpresa",
    "TeamMember",
    # Clientes y vehículos
    "Cliente",
    "Vehiculo",
    "Marca",
    # Kilometraje
    "KilometrajeRegistro",
    "RegistroKilometraje",
    "ChecklistIngreso",
    # Documentos
    "Documento",
    "LineaServicio",
    "LineaRepuesto",
    "LineaOtroServicio",
    # Memoria y seguimiento
    "NotaInterna",
    "EtiquetaInterna",
    "EtiquetaAsignacion",
    "EvidenciaDocumento",
    "SeguimientoPublico",
    # Repuestos
    "Repuesto",
    # Ubicación
    "Estado",
    "Ciudad",
    # Suscripción y pagos
    "ComprobantePago",
    "TrialRegistro",
    # Legacy / compatibilidad
    "LogAuditoria",
    "PagoPendiente",
    "RegimenFiscal",
    "MarcaVehiculo",
    "ModeloVehiculo",
    # Extras de vehículos
    "CajaVehiculo",
    "ColorVehiculo",
    "MotorVehiculo",
]
# Quitar del __all__ los que no se importaron (módulo faltante en servidor)
for _name in ("PagoPendiente", "RegimenFiscal", "MarcaVehiculo", "ModeloVehiculo"):
    if _name in __all__ and globals().get(_name) is None:
        __all__.remove(_name)

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
