# Branding y configuración avanzada
from .company_settings import CompanySettings, CompanySettingsHistory

# Modelos base y mixins
from .mixins import AuditMixin
from .tecnico import Tecnico
# from .tecnico import Tecnico as Mecanico  # alias legacy si es necesario

# Catálogo global
from .catalogo import CatalogoModeloAuto

# Modelos principales
from .documento import Documento
from .configuracion import ConfiguracionEmpresa
from .empresa import Empresa  # re-export para importaciones simples en tests

# Repuestos
from .repuesto import Repuesto, CategoriaRepuesto

# Líneas de documento
from .lineas_documento import LineaRepuesto, LineaServicio, LineaOtroServicio

