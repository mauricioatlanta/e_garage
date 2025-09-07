# Branding y configuración avanzada
# Catálogo global
from .catalogo import CatalogoModeloAuto
from .company_settings import CompanySettings, CompanySettingsHistory
from .configuracion import ConfiguracionEmpresa
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

# from .tecnico import Tecnico as Mecanico  # alias legacy si es necesario
