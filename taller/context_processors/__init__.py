"""Paquete de context processors de ``taller``.

Soluciona conflicto entre un archivo ``context_processors.py`` y este
paquete homónimo que impedía que Django resolviera rutas como
``taller.context_processors.empresa_contexto``. Ahora las funciones se
exponen directamente desde el paquete para que ``import_string`` de
Django obtenga el callable correcto.
"""

from django.core.cache import cache

# Traer la función existente definida en submódulo independiente
from .empresa_contexto import empresa_contexto as _empresa_contexto_impl
from .namespaces import ui_namespaces  # útil para otros settings

__all__ = [
	'empresa_contexto',
	'company_branding',
	'company_country',
	'invalidate_company_cache',
	'ui_namespaces',
]


def empresa_contexto(request):  # noqa: D401
	"""Wrapper que delega en la implementación importada.

	Se define aquí para que el atributo exista en el paquete y Django
	pueda encontrarlo con la ruta acortada utilizada en settings.
	"""
	return _empresa_contexto_impl(request)


def company_branding(request):
	"""Inyecta configuración extendida de branding.

	Usa caché por usuario para reducir consultas.
	Importa el modelo de forma perezosa para evitar ciclos.
	"""
	user = getattr(request, 'user', None)
	if not user or not user.is_authenticated:
		return {
			'company_settings': None,
			'company_name': 'eGarage',
			'company_logo': '/static/images/egarage_default_logo.png',
			'primary_color': '#0d6efd',
			'secondary_color': '#6c757d',
		}

	from taller.models import CompanySettings  # import local lazy

	cache_key = f"company_settings_{user.id}"
	company_settings = cache.get(cache_key)

	if company_settings is None:
		try:
			company_settings = CompanySettings.objects.get(user=user)
			cache.set(cache_key, company_settings, 3600)  # 1 hora
		except CompanySettings.DoesNotExist:
			cache.set(cache_key, 'not_found', 600)
			company_settings = None

	if company_settings == 'not_found':
		company_settings = None

	context = {
		'company_settings': company_settings,
		'company_name': company_settings.get_company_name() if company_settings else 'eGarage',
		'company_logo': company_settings.get_logo_url() if company_settings else '/static/images/egarage_default_logo.png',
		'primary_color': company_settings.get_primary_color() if company_settings else '#0d6efd',
		'secondary_color': company_settings.get_secondary_color() if company_settings else '#6c757d',
	}

	if company_settings:
		context.update({
			'company_tagline': company_settings.tagline,
			'company_address': company_settings.address,
			'company_phone': company_settings.phone,
			'company_email': company_settings.email,
			'company_website': company_settings.website,
			'company_tax_id': company_settings.tax_id,
			'company_currency': company_settings.currency,
			'company_about': company_settings.about_text,
		})

	return context


def invalidate_company_cache(user_id: int):
	"""Invalida caché de branding para un usuario."""
	cache_key = f"company_settings_{user_id}"
	cache.delete(cache_key)


def company_country(request):
	"""
	Context processor para datos específicos del país de la empresa
	"""
	if not getattr(request, 'user', None) or not request.user.is_authenticated:
		return {}
		
	try:
		from taller.models.empresa import Empresa
		from taller.utils.pais_utils import get_configuracion_pais
		
		# Obtener empresa del usuario
		try:
			empresa = Empresa.objects.get(user=request.user)
		except Empresa.DoesNotExist:
			# Fallback: buscar empresa por campo legacy usuario
			empresa = Empresa.objects.filter(usuario=request.user).first()
			if not empresa:
				# Crear empresa básica si no existe
				empresa = Empresa.objects.create(
					user=request.user,
					nombre_taller=f'Taller de {request.user.username}',
					pais='CL'  # Default Chile
				)
	except Exception as e:
		print(f"Error en company_country context processor: {e}")
		return {}
	
	if not empresa:
		return {}
	
	# Obtener configuración del país
	config = get_configuracion_pais(empresa)
	
	# Determinar configuración de impuestos
	country = empresa.pais
	
	# Configuración específica por país
	if country == 'CL':
		# Chile: IVA 19% solo sobre repuestos
		tax_rate = 0.19
		tax_label = "IVA (19%)"
		tax_base = "parts_only"
		unit_label = "Kilometraje"
		distance_field = "kilometraje"
	else:
		# USA: Sales Tax configurable sobre subtotal completo
		tax_rate = config.get('impuesto_default', 0.08)
		tax_label = "Sales Tax"
		tax_base = "subtotal"
		unit_label = "Miles"
		distance_field = "millas"
	
	return {
		'company_country': country,
		'company_config': config,
		'empresa_context': empresa,
		
		# Configuración de impuestos
		'doc_tax_rate': tax_rate,
		'doc_tax_label': tax_label,
		'doc_tax_base': tax_base,
		
		# Configuración de unidades
		'doc_unit_label': unit_label,
		'doc_distance_field': distance_field,
		
		# Configuración de moneda
		'doc_currency_symbol': config.get('simbolo_moneda', '$'),
		'doc_currency_decimals': config.get('decimales', 0),
		
		# Configuración de fecha
		'doc_date_format': config.get('formato_fecha', '%d/%m/%Y'),
	}
