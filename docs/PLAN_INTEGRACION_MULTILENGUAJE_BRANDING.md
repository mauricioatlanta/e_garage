# 🌍 PLAN INTEGRACIÓN MULTILENGUAJE + BRANDING

## 🎯 OBJETIVO: BRANDING PERSONALIZADO + CONTEXTO MULTIPAÍS/IDIOMA

### Escenario de Uso
Un taller (suscriptor) tiene:
- **Su branding corporativo** (logo, colores, nombre empresa)
- **Usuarios en múltiples países** (empleados en Chile y USA)
- **Contenido localizado** (servicios en español/inglés según país)

**Resultado esperado**: Cada usuario ve el branding del taller + contenido de su país/idioma.

## 🔧 IMPLEMENTACIÓN TÉCNICA

### 1. Context Processor Unificado

```python
# taller/context_processors/unified_branding_multilang.py
from django.core.cache import cache
from django.conf import settings
from .country_context import get_country_from_request, get_language_from_request
from taller.models import CompanySettings

def unified_branding_multilang_context(request):
    """
    Context processor que combina:
    - Branding personalizado del suscriptor (si existe)
    - Contexto de país/idioma del usuario actual
    - Defaults inteligentes por país
    """

    # 1. Detectar país/idioma del usuario
    current_country = get_country_from_request(request)
    current_language = get_language_from_request(request)

    # 2. Identificar suscriptor (empresa dueña del sistema)
    subscriber_user = get_subscriber_user(request)

    # 3. Cache key único por suscriptor + país + idioma
    cache_key = f'unified_context_{subscriber_user.id if subscriber_user else "default"}_{current_country}_{current_language}'

    cached_context = cache.get(cache_key)
    if cached_context:
        return cached_context

    # 4. Construir contexto base multilenguaje
    context = {
        # Contexto país/idioma
        'current_country': current_country,
        'current_language': current_language,
        'available_countries': get_available_countries(),
        'country_flag': get_country_flag(current_country),
        'language_name': get_language_display_name(current_language),
        'country_name': get_country_display_name(current_country),

        # URLs localizadas
        'country_url_prefix': f'/{current_country.lower()}',
        'switch_country_urls': get_country_switch_urls(request),

        # Configuración regional
        'currency_symbol': get_currency_for_country(current_country),
        'date_format': get_date_format_for_country(current_country),
        'number_format': get_number_format_for_country(current_country),
    }

    # 5. Agregar branding personalizado del suscriptor
    if subscriber_user:
        try:
            company_settings = CompanySettings.objects.get(user=subscriber_user)

            # Branding visual personalizado
            context.update({
                'company_name': company_settings.get_localized_company_name(current_language),
                'company_tagline': company_settings.get_localized_tagline(current_language),
                'company_logo': company_settings.get_logo_url(),
                'company_favicon': company_settings.get_favicon_url(),

                # Paleta de colores personalizada
                'primary_color': company_settings.primary_color,
                'secondary_color': company_settings.secondary_color,
                'accent_color': company_settings.accent_color,
                'background_color': company_settings.background_color,
                'text_color': company_settings.text_color,

                # Tipografía personalizada
                'font_family': company_settings.get_font_family(),
                'font_size_base': company_settings.font_size_base,
                'font_weight': company_settings.font_weight,

                # Estilo visual
                'border_radius': company_settings.border_radius,
                'shadow_style': company_settings.shadow_style,
                'layout_style': company_settings.layout_style,

                # Información de contacto localizada
                'company_address': company_settings.get_localized_address(current_country),
                'company_phone': company_settings.get_localized_phone(current_country),
                'company_email': company_settings.email,
                'company_website': company_settings.website,

                # Configuración de documentos
                'document_header_style': company_settings.document_header_style,
                'invoice_prefix': company_settings.get_localized_prefix('invoice', current_country),
                'quote_prefix': company_settings.get_localized_prefix('quote', current_country),
                'work_order_prefix': company_settings.get_localized_prefix('work_order', current_country),

                # Flags de personalización
                'has_custom_branding': True,
                'branding_tier': company_settings.get_branding_tier(),
                'customization_level': company_settings.get_customization_level(),
            })

            # CSS Variables dinámicas
            context['css_variables'] = company_settings.get_css_variables()
            context['custom_css'] = company_settings.get_custom_css()

        except CompanySettings.DoesNotExist:
            # Fallback a branding por defecto del país
            context.update(get_default_branding_for_country(current_country))
            context['has_custom_branding'] = False
    else:
        # Usuario no asociado a suscriptor - branding por defecto
        context.update(get_default_branding_for_country(current_country))
        context['has_custom_branding'] = False

    # 6. Configuración de la aplicación
    context.update({
        'app_version': settings.APP_VERSION,
        'support_email': get_support_email_for_country(current_country),
        'help_url': get_help_url_for_language(current_language),
        'terms_url': get_terms_url_for_country(current_country),
    })

    # Cache por 10 minutos
    cache.set(cache_key, context, 600)
    return context

def get_subscriber_user(request):
    """
    Identifica el usuario suscriptor (dueño del branding)
    Puede ser el usuario actual o el propietario del workspace
    """
    if not request.user.is_authenticated:
        return None

    # Si es superuser, no tiene branding personalizado
    if request.user.is_superuser:
        return None

    # Lógica para identificar el suscriptor:
    # 1. Si el usuario tiene CompanySettings, es el suscriptor
    if hasattr(request.user, 'companysettings'):
        return request.user

    # 2. Si es empleado, buscar el propietario del workspace
    if hasattr(request.user, 'employee_profile'):
        return request.user.employee_profile.company_owner

    # 3. Si pertenece a un grupo específico, buscar el admin del grupo
    # (implementar según tu lógica de grupos/organizaciones)

    return request.user  # Default: el mismo usuario

def get_country_switch_urls(request):
    """Genera URLs para cambiar de país manteniendo la página actual"""
    current_path = request.path
    available_countries = get_available_countries()

    urls = {}
    for country in available_countries:
        # Reemplazar prefijo de país en URL
        country_path = f'/{country.lower()}{current_path[3:]}'  # Asume /XX/ al inicio
        urls[country] = {
            'url': country_path,
            'name': get_country_display_name(country),
            'flag': get_country_flag(country)
        }

    return urls
```

### 2. Modelo CompanySettings Extendido para Multilenguaje

```python
# taller/models/company_settings.py - Extensiones multilenguaje
class CompanySettings(models.Model):
    # ... campos existentes ...

    # NUEVOS CAMPOS - Localización multilenguaje
    company_name_es = models.CharField(
        max_length=100,
        blank=True,
        help_text="Nombre de la empresa en español"
    )
    company_name_en = models.CharField(
        max_length=100,
        blank=True,
        help_text="Company name in English"
    )

    tagline_es = models.CharField(
        max_length=200,
        blank=True,
        help_text="Eslogan en español"
    )
    tagline_en = models.CharField(
        max_length=200,
        blank=True,
        help_text="Tagline in English"
    )

    # Direcciones por país
    address_cl = models.TextField(
        blank=True,
        help_text="Dirección en Chile"
    )
    address_us = models.TextField(
        blank=True,
        help_text="Address in USA"
    )
    address_mx = models.TextField(
        blank=True,
        help_text="Dirección en México"
    )

    # Teléfonos por país
    phone_cl = models.CharField(
        max_length=20,
        blank=True,
        help_text="Teléfono Chile (+56)"
    )
    phone_us = models.CharField(
        max_length=20,
        blank=True,
        help_text="Phone USA (+1)"
    )
    phone_mx = models.CharField(
        max_length=20,
        blank=True,
        help_text="Teléfono México (+52)"
    )

    # Prefijos de documentos por país
    invoice_prefix_cl = models.CharField(
        max_length=10,
        default='F',
        help_text="Prefijo facturas Chile"
    )
    invoice_prefix_us = models.CharField(
        max_length=10,
        default='INV',
        help_text="Invoice prefix USA"
    )

    quote_prefix_cl = models.CharField(
        max_length=10,
        default='C',
        help_text="Prefijo cotizaciones Chile"
    )
    quote_prefix_us = models.CharField(
        max_length=10,
        default='QTE',
        help_text="Quote prefix USA"
    )

    # Métodos de localización
    def get_localized_company_name(self, language):
        """Nombre de empresa localizado"""
        if language == 'es' and self.company_name_es:
            return self.company_name_es
        elif language == 'en' and self.company_name_en:
            return self.company_name_en
        return self.company_name  # Fallback

    def get_localized_tagline(self, language):
        """Eslogan localizado"""
        if language == 'es' and self.tagline_es:
            return self.tagline_es
        elif language == 'en' and self.tagline_en:
            return self.tagline_en
        return self.tagline  # Fallback

    def get_localized_address(self, country):
        """Dirección localizada por país"""
        address_field = f'address_{country.lower()}'
        localized_address = getattr(self, address_field, None)
        return localized_address if localized_address else self.address

    def get_localized_phone(self, country):
        """Teléfono localizado por país"""
        phone_field = f'phone_{country.lower()}'
        localized_phone = getattr(self, phone_field, None)
        return localized_phone if localized_phone else self.phone

    def get_localized_prefix(self, document_type, country):
        """Prefijo de documento localizado"""
        prefix_field = f'{document_type}_prefix_{country.lower()}'
        localized_prefix = getattr(self, prefix_field, None)
        if localized_prefix:
            return localized_prefix

        # Fallback a prefijo general
        return getattr(self, f'{document_type}_prefix', 'DOC')

    def get_branding_summary(self, country, language):
        """Resumen completo de branding para país/idioma específico"""
        return {
            'company_name': self.get_localized_company_name(language),
            'tagline': self.get_localized_tagline(language),
            'address': self.get_localized_address(country),
            'phone': self.get_localized_phone(country),
            'email': self.email,
            'website': self.website,
            'logo_url': self.get_logo_url(),
            'primary_color': self.primary_color,
            'secondary_color': self.secondary_color,
            'font_family': self.get_font_family(),
            'css_variables': self.get_css_variables(),
        }
```

### 3. Template Base Unificado

```html
<!-- templates/base_unified.html -->
<!DOCTYPE html>
<html lang="{{ current_language }}" data-country="{{ current_country }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <!-- Título dinámico con branding -->
    <title>
        {% block title %}{{ company_name }}{% if has_custom_branding %} | {{ company_tagline }}{% endif %}{% endblock %}
    </title>

    <!-- Favicon personalizado -->
    {% if company_favicon %}
        <link rel="icon" href="{{ company_favicon }}" type="image/x-icon">
    {% else %}
        <link rel="icon" href="{% url 'static' %}img/favicon-{{ current_country|lower }}.ico">
    {% endif %}

    <!-- CSS Variables dinámicas -->
    <style>
        :root {
            /* Branding colors */
            --primary-color: {{ primary_color }};
            --secondary-color: {{ secondary_color }};
            --accent-color: {{ accent_color }};
            --background-color: {{ background_color }};
            --text-color: {{ text_color }};

            /* Typography */
            --font-family: {{ font_family }};
            --font-size-base: {{ font_size_base }}px;

            /* Visual style */
            --border-radius: {{ border_radius }}px;
            --shadow-style: {{ shadow_style }};

            /* Country-specific */
            --country-code: "{{ current_country }}";
            --language-code: "{{ current_language }}";
            --currency-symbol: "{{ currency_symbol }}";
        }

        {% if has_custom_branding %}
        /* CSS personalizado del suscriptor */
        {{ custom_css|safe }}
        {% endif %}

        /* Estilos específicos por país */
        body[data-country="CL"] {
            --accent-secondary: #d32f2f; /* Rojo chileno */
        }

        body[data-country="US"] {
            --accent-secondary: #1565c0; /* Azul americano */
        }
    </style>

    <!-- Bootstrap y CSS base -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">

    <!-- Google Fonts (si se usa tipografía personalizada) -->
    {% if font_family != 'system' %}
        <link href="https://fonts.googleapis.com/css2?family={{ font_family|urlencode }}:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    {% endif %}

    {% block extra_css %}{% endblock %}
</head>

<body data-country="{{ current_country }}" data-language="{{ current_language }}" {% if has_custom_branding %}data-custom-branding="true"{% endif %}>

    <!-- Header con branding personalizado -->
    <header class="main-header">
        <nav class="navbar navbar-expand-lg">
            <div class="container">
                <!-- Logo + Nombre empresa -->
                <a class="navbar-brand" href="{{ country_url_prefix }}/">
                    {% if company_logo %}
                        <img src="{{ company_logo }}" alt="{{ company_name }}" class="brand-logo">
                    {% endif %}
                    <span class="brand-text">{{ company_name }}</span>
                    {% if company_tagline %}
                        <small class="brand-tagline d-none d-md-inline">{{ company_tagline }}</small>
                    {% endif %}
                </a>

                <!-- Selector de país/idioma -->
                <div class="country-language-selector">
                    <div class="dropdown">
                        <button class="btn btn-outline-secondary dropdown-toggle" type="button" data-bs-toggle="dropdown">
                            <span class="flag-icon flag-icon-{{ current_country|lower }}"></span>
                            {{ country_name }} ({{ current_language|upper }})
                        </button>
                        <ul class="dropdown-menu">
                            {% for country_code, country_info in switch_country_urls.items %}
                                <li>
                                    <a class="dropdown-item" href="{{ country_info.url }}">
                                        <span class="flag-icon flag-icon-{{ country_code|lower }}"></span>
                                        {{ country_info.name }}
                                    </a>
                                </li>
                            {% endfor %}
                        </ul>
                    </div>
                </div>

                <!-- Navegación principal -->
                <div class="navbar-nav ms-auto">
                    <a class="nav-link" href="{{ country_url_prefix }}/dashboard/">
                        <i class="fas fa-tachometer-alt"></i>
                        {% if current_language == 'es' %}Dashboard{% else %}Dashboard{% endif %}
                    </a>
                    <a class="nav-link" href="{{ country_url_prefix }}/clients/">
                        <i class="fas fa-users"></i>
                        {% if current_language == 'es' %}Clientes{% else %}Clients{% endif %}
                    </a>
                    <a class="nav-link" href="{{ country_url_prefix }}/services/">
                        <i class="fas fa-wrench"></i>
                        {% if current_language == 'es' %}Servicios{% else %}Services{% endif %}
                    </a>

                    <!-- Settings (solo para suscriptores) -->
                    {% if has_custom_branding and user.companysettings %}
                        <a class="nav-link" href="{{ country_url_prefix }}/settings/">
                            <i class="fas fa-cog"></i>
                            {% if current_language == 'es' %}Configuración{% else %}Settings{% endif %}
                        </a>
                    {% endif %}
                </div>
            </div>
        </nav>
    </header>

    <!-- Contenido principal -->
    <main class="main-content">
        {% block content %}{% endblock %}
    </main>

    <!-- Footer con información localizada -->
    <footer class="main-footer">
        <div class="container">
            <div class="row">
                <div class="col-md-6">
                    <div class="footer-company-info">
                        <h6>{{ company_name }}</h6>
                        {% if company_address %}
                            <p class="mb-1">
                                <i class="fas fa-map-marker-alt"></i>
                                {{ company_address }}
                            </p>
                        {% endif %}
                        {% if company_phone %}
                            <p class="mb-1">
                                <i class="fas fa-phone"></i>
                                {{ company_phone }}
                            </p>
                        {% endif %}
                        {% if company_email %}
                            <p class="mb-1">
                                <i class="fas fa-envelope"></i>
                                {{ company_email }}
                            </p>
                        {% endif %}
                    </div>
                </div>
                <div class="col-md-6 text-end">
                    <div class="footer-meta">
                        <p class="mb-1">
                            {% if current_language == 'es' %}
                                Powered by eGarage v{{ app_version }}
                            {% else %}
                                Powered by eGarage v{{ app_version }}
                            {% endif %}
                        </p>
                        <p class="mb-0">
                            <a href="{{ terms_url }}" class="text-muted">
                                {% if current_language == 'es' %}Términos{% else %}Terms{% endif %}
                            </a>
                            |
                            <a href="{{ help_url }}" class="text-muted">
                                {% if current_language == 'es' %}Ayuda{% else %}Help{% endif %}
                            </a>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </footer>

    <!-- JavaScript -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>

    <!-- Context JavaScript global -->
    <script>
        window.eGarageContext = {
            country: '{{ current_country }}',
            language: '{{ current_language }}',
            hasCustomBranding: {{ has_custom_branding|yesno:"true,false" }},
            companyName: '{{ company_name|escapejs }}',
            currencySymbol: '{{ currency_symbol }}',
            apiEndpoints: {
                services: '{{ country_url_prefix }}/api/services/',
                clients: '{{ country_url_prefix }}/api/clients/',
                search: '{{ country_url_prefix }}/api/search/',
            }
        };
    </script>

    {% block extra_js %}{% endblock %}
</body>
</html>
```

### 4. URLs Multipaís Actualizadas

```python
# egarage/urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from taller.views import home_redirect

urlpatterns = [
    path('admin/', admin.site.urls),

    # Redirect root to default country
    path('', home_redirect, name='home_redirect'),

    # Country-specific URLs
    path('cl/', include('taller.urls.chile')),  # Chile (español)
    path('us/', include('taller.urls.usa')),    # USA (inglés)
    path('mx/', include('taller.urls.mexico')), # México (español)

    # API global (sin país específico)
    path('api/', include('taller.api.urls')),

    # Settings global para suscriptores
    path('settings/', include('taller.urls.settings')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# taller/urls/chile.py
from django.urls import path, include
from taller.views import dashboard_cl, services_cl, clients_cl

app_name = 'chile'

urlpatterns = [
    path('', dashboard_cl, name='dashboard'),
    path('clientes/', clients_cl, name='clients'),
    path('servicios/', services_cl, name='services'),
    path('documentos/', include('taller.urls.documents_cl')),
    path('reportes/', include('taller.urls.reports_cl')),
]

# taller/urls/usa.py
from django.urls import path, include
from taller.views import dashboard_us, services_us, clients_us

app_name = 'usa'

urlpatterns = [
    path('', dashboard_us, name='dashboard'),
    path('clients/', clients_us, name='clients'),
    path('services/', services_us, name='services'),
    path('documents/', include('taller.urls.documents_us')),
    path('reports/', include('taller.urls.reports_us')),
]
```

## 🎯 CASOS DE USO ESPECÍFICOS

### Caso 1: Taller "AutoFix Chile" con empleados en CL y US

**Configuración**:
- Suscriptor: `autofix_admin` (dueño del branding)
- Empleados: `juan_cl` (Chile), `mike_us` (USA)
- Branding: Logo AutoFix, colores rojo/azul, nombre "AutoFix Chile"

**Comportamiento**:
- `juan_cl` accede a `/cl/` → Ve branding AutoFix + servicios en español
- `mike_us` accede a `/us/` → Ve branding AutoFix + servicios en inglés
- Ambos ven mismo logo, colores, nombre empresa
- PDFs generados mantienen branding consistente

### Caso 2: Franquicia "QuickLube" en múltiples países

**Configuración**:
- Suscriptor: `quicklube_master`
- Franquicias: Chile, USA, México
- Branding uniforme pero datos de contacto localizados

**Comportamiento**:
- Mismo logo y colores en todos los países
- Direcciones y teléfonos específicos por país
- Documentos con encabezados localizados
- Monedas y formatos según país

## 🚀 BENEFICIOS DE LA INTEGRACIÓN

### Para Desarrolladores
- ✅ Un solo context processor maneja todo
- ✅ Templates unificados, menos duplicación
- ✅ Cache inteligente optimiza performance
- ✅ Escalable a nuevos países/idiomas

### Para Suscriptores
- ✅ Branding consistente en todos los mercados
- ✅ Datos localizados automáticamente
- ✅ Configuración centralizada pero flexible
- ✅ Documentos profesionales por país

### Para Usuarios Finales
- ✅ Experiencia visual coherente
- ✅ Contenido en su idioma y contexto
- ✅ Información relevante por país
- ✅ Performance optimizada

**¿Quieres que implemente esta integración completa? Con esto tendrás el sistema de branding más avanzado y escalable del mercado.** 🎯
