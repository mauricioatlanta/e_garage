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
from .modelo import Modelo

# Modelos de kilometraje
from .kilometraje import KilometrajeRegistro

# Modelos de documentos
from .documento import Documento
from .lineas_documento import LineaServicio, LineaRepuesto, LineaOtroServicio
from .correlativo import CorrelativoDocumento

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
from .pieza_desarme import (
    PiezaDesarme,
    PiezaDesarmeName,
    PiezaDesarmeCompanyLabel,
    PrecioHistoricoPieza,
)
from .vehiculo_desarme import VehiculoDesarme
from .vehiculo_financial import (
    VehiculoFinancialSnapshot,
    VehicleFinancialEvent,
)
from .vendedor_desarme import VendedorDesarme

# Modelos de ubicación
from .ubicacion import Estado, Ciudad

# Modelos de suscripción y pagos
from .comprobante_pago import ComprobantePago
from .suscripcion_transaccion import SuscripcionTransaccion
from .trial import TrialRegistro

# Modelos legacy / compatibilidad (deben importarse para que Django los registre)
from .auditoria import LogAuditoria
from .pago import PagoPendiente
from .regimen_fiscal import RegimenFiscal
from .marcas_usa import MarcaVehiculo, ModeloVehiculo

# Modelos de extras de vehículos
from .extras_vehiculo import (
    CajaVehiculo,
    CajaVehiculoEmpresa,
    ColorVehiculo,
    MotorVehiculo,
    MotorVehiculoEmpresa,
)

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
    "Modelo",
    # Kilometraje
    "KilometrajeRegistro",
    # Documentos
    "Documento",
    "LineaServicio",
    "LineaRepuesto",
    "LineaOtroServicio",
    "CorrelativoDocumento",
    # Memoria y seguimiento
    "NotaInterna",
    "EtiquetaInterna",
    "EtiquetaAsignacion",
    "EvidenciaDocumento",
    "SeguimientoPublico",
    # Repuestos
    "Repuesto",
    "PiezaDesarme",
    "PiezaDesarmeName",
    "PiezaDesarmeCompanyLabel",
    "PrecioHistoricoPieza",
    "VehiculoDesarme",
    "VehiculoFinancialSnapshot",
    "VehicleFinancialEvent",
    "VendedorDesarme",
    # Ubicación
    "Estado",
    "Ciudad",
    # Suscripción y pagos
    "ComprobantePago",
    "SuscripcionTransaccion",
    "TrialRegistro",
    # Legacy / compatibilidad
    "LogAuditoria",
    "PagoPendiente",
    "RegimenFiscal",
    "MarcaVehiculo",
    "ModeloVehiculo",
    # Extras de vehículos
    "CajaVehiculo",
    "CajaVehiculoEmpresa",
    "ColorVehiculo",
    "MotorVehiculo",
    "MotorVehiculoEmpresa",
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
