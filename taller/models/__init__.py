# Branding y configuración avanzada
# Catálogo global
from .catalogo import CatalogoModeloAuto
from .clientes import Cliente
from .company_settings import CompanySettings, CompanySettingsHistory
from .configuracion import ConfiguracionEmpresa

# Modelos de ubicación (Estado y Ciudad mejorados con soporte multi-país)
# Address está en la app ubicacion separada
from .ubicacion import Ciudad, Estado

# Catálogo de Repuestos y Servicios con I18N
from .catalogo_repuestos import Part, PartI18N, PartPrice, TaxPolicy
from .catalogo_servicios import Service, ServiceI18N, ServicePrice

# Modelos principales
from .documento import Documento
from .empresa import Empresa  # re-export para importaciones simples en tests

# Líneas de documento
from .lineas_documento import LineaOtroServicio, LineaRepuesto, LineaServicio

# Modelos base y mixins
from .mixins import AuditMixin

# Repuestos
from .repuesto import CategoriaRepuesto, Repuesto
from .tecnico import Tecnico
from .vehiculos import Vehiculo

# from .tecnico import Tecnico as Mecanico  # alias legacy si es necesario
