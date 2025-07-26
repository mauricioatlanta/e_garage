from .repuesto import Repuesto
from .empresa import Empresa
from .trial import TrialRegistro
from .comprobante_pago import ComprobantePago
from .perfil_usuario import PerfilUsuario
from .mecanico import Mecanico

from .clientes import Cliente
from .vehiculos import Vehiculo

# Modelos de ubicación USA
from .ubicacion import Estado, Ciudad

# Modelos de vehículos USA  
from .marcas_usa import MarcaVehiculo, ModeloVehiculo

# Exponer modelos principales para importación directa
from .documento import Documento, RepuestoDocumento, ServicioDocumento
from .auditoria import LogAuditoria
from .notificacion import TipoNotificacion, NotificacionEnviada, ConfiguracionNotificacion, RecordatorioMantenimiento

from .venta import Venta

