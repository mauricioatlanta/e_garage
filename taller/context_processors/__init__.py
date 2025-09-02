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

# Definir nuestro context processor personalizado directamente aquí


def company_context(request):
    """Context processor para datos de empresa y configuración estática."""
    empresa = getattr(request.user, "empresa", None) if hasattr(request, 'user') and request.user.is_authenticated else None
    country = getattr(empresa, "pais", "CL") if empresa else "CL"
    company_settings = getattr(empresa, "configuracion", None) if empresa else None
    return {
        "country": country,
        "company_settings": company_settings,
        "STATIC_VERSION": "dev",
        "company": getattr(request, "company", None),
    }


def company_branding_context(request):
    """
    Context processor global para inyectar información de empresa en todas las plantillas.
    Proporciona company_name y company_logo_url de forma consistente.
    """
    # DEBUG: Agregar logging temporal
    print(f"🔍 DEBUG: Context processor llamado para usuario: {getattr(request, 'user', None)}")
    print(f"🔍 DEBUG: Context processor EJECUTÁNDOSE - INICIO")
    
    # No aplicar en rutas sin usuario
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        print(f"🔍 DEBUG: Usuario no autenticado, retornando vacío")
        return {}

    empresa = getattr(user, "empresa", None)
    if not empresa:
        print(f"🔍 DEBUG: Usuario sin empresa, retornando vacío")
        return {}

    # Usa cache leve por request.user.empresa_id y país para performance
    country = getattr(request, "country", None) or getattr(request, "COUNTRY", None) or "NA"
    cache_key = f"ctx_company:{empresa.id}:{country}"
    
    print(f"🔍 DEBUG: Cache key: {cache_key}")
    
    data = cache.get(cache_key)
    if data:
        print(f"🔍 DEBUG: Cache hit, retornando: {data}")
        return data

    print(f"🔍 DEBUG: Cache miss, calculando datos...")

    # Origen de verdad: ConfiguracionEmpresa (modelo legacy que se usa actualmente)
    company_name = ""
    logo_url = ""

    try:
        # Intentar obtener configuración de empresa de forma robusta
        configuracion = None
        for attr in ("config", "configuracion", "settings", "configuracionempresa", "companysettings"):
            configuracion = getattr(empresa, attr, None)
            if configuracion:
                print(f"🔍 DEBUG: Configuración encontrada en atributo: {attr}")
                break
        
        # Si no se encuentra, buscar directamente en la base de datos
        if not configuracion:
            from taller.models import ConfiguracionEmpresa
            configuracion = ConfiguracionEmpresa.objects.filter(empresa=empresa).first()
            print(f"🔍 DEBUG: Configuración buscada en BD: {configuracion}")
        
        if configuracion:
            # Usar nombre_publico si existe, sino usar nombre_taller de empresa
            company_name = getattr(configuracion, "nombre_publico", "") or getattr(empresa, "nombre_taller", "")
            
            # Obtener URL del logo de forma robusta
            logo_field = getattr(configuracion, "logo", None)
            print(f"🔍 DEBUG: Logo field: {logo_field}")
            if logo_field and hasattr(logo_field, "url"):
                try:
                    logo_url = logo_field.url
                    print(f"🔍 DEBUG: Logo URL obtenida: {logo_url}")
                except (ValueError, AttributeError) as e:
                    print(f"🔍 DEBUG: Error obteniendo logo URL: {e}")
                    logo_url = ""
            else:
                print(f"🔍 DEBUG: No hay logo field o no tiene URL")
                logo_url = ""
        else:
            # Fallback: usar datos directos de empresa
            company_name = getattr(empresa, "nombre_taller", "")
            logo_field = getattr(empresa, "logo", None)
            if logo_field and hasattr(logo_field, "url"):
                try:
                    logo_url = logo_field.url
                except (ValueError, AttributeError):
                    logo_url = ""
            else:
                logo_url = ""
                    
    except Exception as e:
        print(f"🔍 DEBUG: Error obteniendo datos: {e}")
        # Fallback en caso de error
        company_name = getattr(empresa, "nombre_taller", "")
        logo_url = ""

    # Preparar datos para cache
    data = {
        "company_name": company_name or "eGarage",
        "company_logo_url": logo_url,
    }
    
    print(f"🔍 DEBUG: Datos calculados: {data}")
    print(f"🔍 DEBUG: company_name final: '{data['company_name']}'")
    print(f"🔍 DEBUG: company_logo_url final: '{data['company_logo_url']}'")
    print(f"🔍 DEBUG: Context processor EJECUTÁNDOSE - FIN")
    
    # Cache por 60 segundos
    cache.set(cache_key, data, 60)
    return data

__all__ = [
	'empresa_contexto',
	'company_branding',
	'company_country',
	'company_context',  # Agregar company_context
	'company_branding_context',  # Agregar nuestro context processor
	'invalidate_company_cache',
	'invalidate_company_branding_cache',  # Agregar función de invalidación
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


def invalidate_company_branding_cache(empresa_id, request=None):
	"""
	Invalida el cache del context processor para una empresa específica.
	Llamar después de actualizar nombre o logo de empresa.
	"""
	# Invalidar para todos los países conocidos
	countries = ["CL", "US", "NA"]
	for country in countries:
		cache_key = f"ctx_company:{empresa_id}:{country}"
		cache.delete(cache_key)
		print(f"🔍 DEBUG: Cache invalidado: {cache_key}")


def company_country(request):
	"""
	Context processor para datos específicos del país de la empresa
	"""
	if not getattr(request, 'user', None) or not request.user.is_authenticated:
		return {}
		
	try:
		from taller.models.empresa import Empresa
		from taller.utils.pais_utils import get_configuracion_pais
		
		# DEBUG: Agregar logs
		print(f"🔍 DEBUG Context Processor - Usuario: {request.user.username}")
		
		# Obtener empresa del usuario
		try:
			empresa = Empresa.objects.get(user=request.user)
			print(f"🔍 DEBUG - Empresa encontrada: {empresa.nombre_taller}, País: {empresa.pais}")
		except Empresa.DoesNotExist:
			print(f"🔍 DEBUG - Empresa no encontrada para user field, buscando en usuario field")
			# Fallback: buscar empresa por campo legacy usuario
			empresa = Empresa.objects.filter(usuario=request.user).first()
			if not empresa:
				print(f"🔍 DEBUG - No hay empresa, creando nueva")
				# Detectar país basándose en el usuario o URL
				default_country = 'CL'  # Default Chile
				
				# Detectar país por nombre de usuario
				if 'usa' in request.user.username.lower():
					default_country = 'US'
					print(f"🔍 DEBUG - Detectado 'usa' en username, país: {default_country}")
				elif 'us' in request.user.username.lower():
					default_country = 'US'
					print(f"🔍 DEBUG - Detectado 'us' en username, país: {default_country}")
				elif 'america' in request.user.username.lower():
					default_country = 'US'
					print(f"🔍 DEBUG - Detectado 'america' en username, país: {default_country}")
				
				# Detectar país por URL path
				path = request.path
				if path.startswith('/us/'):
					default_country = 'US'
					print(f"🔍 DEBUG - Detectado '/us/' en path, país: {default_country}")
				elif path.startswith('/cl/'):
					default_country = 'CL'
					print(f"🔍 DEBUG - Detectado '/cl/' en path, país: {default_country}")
				
				print(f"🔍 DEBUG - País final detectado: {default_country}")
				
				# Crear empresa básica si no existe
				empresa = Empresa.objects.create(
					user=request.user,
					nombre_taller=f'Taller de {request.user.username}',
					pais=default_country
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
	print(f"🔍 DEBUG - País final de empresa: {country}")
	
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
	
	result = {
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
	
	print(f"🔍 DEBUG - Context processor result: company_country = {result['company_country']}")
	return result
