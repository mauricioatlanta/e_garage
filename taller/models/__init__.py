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
from .vehiculo_imagen import VehiculoImagen
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
from .interchange_pieza import InterchangePieza
from .sugerencia_pieza_desarme import SugerenciaPiezaDesarme
from .vehiculo_desarme import VehiculoDesarme, EstadoOperativo
from .vehiculo_desarme_event import VehiculoDesarmeEvent, TipoEventoDesarme
from .catalogo_repuesto_empresa import CatalogoRepuestoEmpresa
from .vehiculo_financial import (
    VehiculoFinancialSnapshot,
    VehicleFinancialEvent,
)
from .smart_yard_global import SmartYardGlobalMetric
from .vendedor_desarme import VendedorDesarme

# Modelos de reciclaje (Atlanta Reciclajes — chatarra electrónica y catalíticos)
from .reciclaje import (
    CategoriaChatarra,
    ProductoChatarra,
    Catalitico,
    PrecioMetal,
    CompraReciclaje,
    DetalleCompraCatalitico,
    DetalleCompraChatarra,
    VentaReciclaje,
    DetalleVentaCatalitico,
    DetalleVentaChatarra,
)
from .venta_desarme import VentaDesarme, LineaVentaDesarme

# Modelos de ubicación
from .ubicacion import Estado, Ciudad

# Modelos de suscripción y pagos
from .comprobante_pago import ComprobantePago
from .suscripcion_transaccion import SuscripcionTransaccion
from .subscription_change import SubscriptionChange
from .trial import TrialRegistro

# Modelos legacy / compatibilidad (deben importarse para que Django los registre)
from .auditoria import LogAuditoria
from .pago import PagoPendiente
from .regimen_fiscal import RegimenFiscal
from .marcas_usa import MarcaVehiculo, ModeloVehiculo
from .comision import ConfiguracionComisionEmpresa, VendedorComision
from .alias_repuesto import AliasRepuesto

# Inspección de ingreso de vehículos
from .inspeccion_ingreso import InspeccionIngreso, DanoInspeccion, EvidenciaInspeccion

# Dominios personalizados
from .empresa_dominio import EmpresaDominio

# Trust & Security
from .sesion_usuario import SesionUsuario

# Embudo de adquisición / registro
from .registro_embudo import RegistroEmbudoSuscriptor

# Analytics público
from .public_page_view import PublicPageView, is_probable_bot

# Sistema de notificaciones
from .notificacion import (
    TipoNotificacion,
    NotificacionEnviada,
    ConfiguracionNotificacion,
    RecordatorioMantenimiento,
)

# WhatsApp admin notification log (tabla en taller, código en taller.whatsapp)
from ..whatsapp.models import WhatsAppAdminNotificationLog

# Ledger de movimientos de inventario
from .movimiento_inventario import MovimientoInventario

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
    "VehiculoImagen",
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
    "InterchangePieza",
    "SugerenciaPiezaDesarme",
    "VehiculoDesarme",
    "CatalogoRepuestoEmpresa",
    "VehiculoFinancialSnapshot",
    "VehicleFinancialEvent",
"SmartYardGlobalMetric",
    "VendedorDesarme",
    # Reciclaje (Atlanta Reciclajes)
    "CategoriaChatarra",
    "ProductoChatarra",
    "Catalitico",
    "PrecioMetal",
    "CompraReciclaje",
    "DetalleCompraCatalitico",
    "DetalleCompraChatarra",
    "VentaReciclaje",
    "DetalleVentaCatalitico",
    "DetalleVentaChatarra",
    # Ubicación
    "Estado",
    "Ciudad",
    # Suscripción y pagos
    "ComprobantePago",
    "SuscripcionTransaccion",
    "SubscriptionChange",
    "TrialRegistro",
    # Legacy / compatibilidad
    "LogAuditoria",
    "PagoPendiente",
    "RegimenFiscal",
    "MarcaVehiculo",
    "ModeloVehiculo",
    # Kiosko / comisiones
    "ConfiguracionComisionEmpresa",
    "VendedorComision",
    "AliasRepuesto",
    # Inspección de ingreso
    "InspeccionIngreso",
    "DanoInspeccion",
    "EvidenciaInspeccion",
    # Dominios personalizados
    "EmpresaDominio",
    # Extras de vehículos
    "CajaVehiculo",
    "CajaVehiculoEmpresa",
    "ColorVehiculo",
    "MotorVehiculo",
    "MotorVehiculoEmpresa",
    # Ledger de inventario
    "MovimientoInventario",
    # Trust & Security
    "SesionUsuario",
    # Embudo de adquisición / registro
    "RegistroEmbudoSuscriptor",
    # Analytics público
    "PublicPageView",
    # Notificaciones
    "TipoNotificacion",
    "NotificacionEnviada",
    "ConfiguracionNotificacion",
    "RecordatorioMantenimiento",
    "WhatsAppAdminNotificationLog",
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
