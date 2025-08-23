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
