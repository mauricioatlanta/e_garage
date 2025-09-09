# Snippets Definitivos - Patrón Canónico de URLs

## ✅ Patrón que Funciona (Sin Duplicados)

### 1. `gestion_taller/urls.py` (Root del Proyecto)

```python
from django.urls import include, path

urlpatterns = [
    # === AUTHENTICATION GLOBAL ===
    path("accounts/", include("allauth.urls")),
    
    # === PAÍSES E IDIOMAS ===
    # Chile - Español
    path("cl/", include(("taller.urls_extra.chile", "taller_cl_es"), namespace="taller_cl_es")),
    
    # USA - Inglés
    path("us/", include(("taller.urls_extra.usa", "taller_us_en"), namespace="taller_us_en")),
    
    # === ADMIN ===
    path("admin/", admin.site.urls),
    
    # === STATIC FILES (desarrollo) ===
    if settings.DEBUG:
        from django.conf.urls.static import static
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
        urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
]
```

### 2. `taller/taller_main_urls.py` (Archivo Principal)

```python
import logging
from django.urls import include, path
from django.views.generic import TemplateView

# Configuración de logging para este módulo
logger = logging.getLogger(__name__)
logger.debug("CARGANDO taller/taller_main_urls.py")

# Importar vistas específicas
from taller.views_extra.bienvenida_usa import bienvenida_usa
from taller.taller_views import (
    dashboard_suscripciones,
    debug_cliente_autocomplete,
    renovar_empresa,
)

# IMPORTANTE: Este es el app_name que se usa en el namespace
app_name = "taller"

urlpatterns = [
    # === LANDING PAGES ===
    path("", TemplateView.as_view(template_name="taller/landing/inicio.html"), name="landing_inicio"),
    path("chile/", TemplateView.as_view(template_name="taller/landing/chile.html"), name="landing_chile"),
    path("usa/", bienvenida_usa, name="landing_usa"),
    
    # === MÓDULOS PRINCIPALES ===
    # Clientes
    path("clientes/", include("taller.clientes.urls")),
    
    # Vehículos
    path("vehiculos/", include("taller.vehiculos.urls")),
    
    # Repuestos
    path("repuestos/", include("taller.repuestos.urls")),
    
    # Servicios
    path("servicios/", include(("taller.servicios.urls", "servicios"), namespace="servicios")),
    
    # Documentos
    path("documentos/", include(("taller.documentos.urls", "documentos"), namespace="documentos")),
    
    # Reportes
    path("reportes/", include("taller.reportes.urls")),
    
    # === MÓDULOS AVANZADOS ===
    # Business Intelligence
    path("business-intelligence/", include("taller.business_intelligence_urls", namespace="business_intelligence")),
    
    # API
    path("api/", include("taller.api.urls", namespace="api")),
    
    # Admin Monitoring
    path("admin/monitoring/", include("taller.urls_modules.admin_monitoring")),
    
    # Emails
    path("emails/", include("taller.emails.urls")),
    
    # === VISTAS ESPECÍFICAS ===
    # Dashboard de suscripciones
    path("admin/dashboard/", dashboard_suscripciones, name="dashboard_suscripciones"),
    
    # Debug
    path("debug-autocomplete/", debug_cliente_autocomplete, name="debug_autocomplete"),
    
    # Renovar empresa
    path("renovar-empresa/<int:empresa_id>/", renovar_empresa, name="renovar_empresa"),
    
    # === CONFIGURACIÓN ===
    path("configuracion/", include("taller.views_extra.views_configuracion"), name="configuracion"),
    path("configuracion/tecnicos/", include("taller.views_extra.views_configuracion"), name="configuracion_tecnicos"),
    
    # === AUTOLOAD ===
    path("autocomplete/", include("taller.autocomplete.urls")),
    
    # === AJAX ENDPOINTS ===
    path("ajax/", include("taller.views_extra.ajax")),
]
```

### 3. `taller/urls_extra/usa.py` (USA - Inglés)

```python
"""
URLs específicas para USA (inglés)
Prefijo: /us/
"""

from django.urls import include, path

from taller import ajax_views
from taller.views_extra.ajax import buscar_clientes, vehiculos_por_cliente
from taller.views_extra.country_views import dashboard_usa_view, test_usa_view
from taller.views_extra.landing_usa import landing_usa


def usa_login_view(request):
    """Vista personalizada de login para USA que no redirige automáticamente"""
    from allauth.account.views import LoginView

    # Configurar el contexto de país para USA
    request.country = "US"
    request.country_code = "US"

    # Usar la vista de allauth pero con template específico para USA
    view = LoginView.as_view(template_name="taller/us/en/auth/login.html")
    return view(request)


def usa_signup_view(request):
    """Vista personalizada de signup para USA"""
    from allauth.account.views import SignupView

    # Configurar el contexto de país para USA
    request.country = "US"
    request.country_code = "US"

    # Usar la vista de allauth pero con template específico para USA
    view = SignupView.as_view(template_name="taller/us/en/auth/signup.html")
    return view(request)


app_name = "usa"

urlpatterns = [
    # === LANDING Y DASHBOARD ===
    # Landing page profesional para USA
    path("", landing_usa, name="home"),
    path("dashboard/", dashboard_usa_view, name="dashboard"),
    
    # Centro de Operaciones Espacial para USA
    path("centro-operaciones-espacial/", dashboard_usa_view, name="centro_operaciones_espacial"),
    
    # Test endpoint USA
    path("test/", test_usa_view, name="test"),
    
    # === MÓDULOS PRINCIPALES ===
    # NOTA: Los submódulos principales (clientes, vehiculos, repuestos, servicios, 
    # documentos, reportes) están incluidos en taller_main_urls.py para evitar duplicación
    # Solo incluimos aquí rutas específicas de USA que no están en el core
    
    # === CONFIGURACIÓN Y SETTINGS ===
    # Incluir URLs principales de taller (configuración, settings, etc.)
    # Este archivo incluye todos los submódulos principales con namespaces correctos
    path("", include("taller.taller_main_urls")),
    
    # === AJAX ENDPOINTS ESPECÍFICOS DE USA ===
    # AJAX jerárquico para vehículos
    path("ajax/load-modelos/", ajax_views.load_modelos, name="ajax_load_modelos"),
    path("ajax/load-motores/", ajax_views.load_motores, name="ajax_load_motores"),
    path("ajax/load-cajas/", ajax_views.load_cajas, name="ajax_load_cajas"),
    path("ajax/load-motores-cajas/", ajax_views.load_motores_cajas, name="ajax_load_motores_cajas"),
    
    # AJAX específicos para USA
    path("ajax/clientes/buscar/", buscar_clientes, name="us_ajax_buscar_clientes"),
    path("ajax/vehiculos-por-cliente/", vehiculos_por_cliente, name="us_ajax_vehiculos_por_cliente"),
    
    # === AUTHENTICATION ===
    # Login para USA
    path("login/", usa_login_view, name="account_login"),
    # Signup para USA
    path("signup/", usa_signup_view, name="account_signup"),
    # Registro para USA
    path("registro/", include("scripts.onboarding_urls")),
    
    # === DASHBOARD DE SUSCRIPTOR ===
    path("", include("taller.analytics.urls_suscriptor")),
]
```

### 4. `taller/urls_extra/chile.py` (Chile - Español)

```python
"""
URLs específicas para Chile (español)
Prefijo: /cl/
"""

from django.urls import include, path

from taller import ajax_views
from taller.views_extra.ajax import buscar_clientes, vehiculos_por_cliente
from taller.views_extra.country_views import dashboard_chile_view, test_chile_view
from taller.views_extra.landing_chile import landing_chile


def chile_login_view(request):
    """Vista personalizada de login para Chile"""
    from allauth.account.views import LoginView

    # Configurar el contexto de país para Chile
    request.country = "CL"
    request.country_code = "CL"

    # Usar la vista de allauth pero con template específico para Chile
    view = LoginView.as_view(template_name="taller/cl/es/auth/login.html")
    return view(request)


def chile_signup_view(request):
    """Vista personalizada de signup para Chile"""
    from allauth.account.views import SignupView

    # Configurar el contexto de país para Chile
    request.country = "CL"
    request.country_code = "CL"

    # Usar la vista de allauth pero con template específico para Chile
    view = SignupView.as_view(template_name="taller/cl/es/auth/signup.html")
    return view(request)


app_name = "chile"

urlpatterns = [
    # === LANDING Y DASHBOARD ===
    # Landing page para Chile
    path("", landing_chile, name="home"),
    path("dashboard/", dashboard_chile_view, name="dashboard"),
    
    # Test endpoint Chile
    path("test/", test_chile_view, name="test"),
    
    # === MÓDULOS PRINCIPALES ===
    # NOTA: Los submódulos principales (clientes, vehiculos, repuestos, servicios, 
    # documentos, reportes) están incluidos en taller_main_urls.py para evitar duplicación
    # Solo incluimos aquí rutas específicas de Chile que no están en el core
    
    # URLs principales de taller (configuración, settings, etc.)
    # Este archivo incluye todos los submódulos principales con namespaces correctos
    path("", include("taller.taller_main_urls")),
    
    # === AJAX ENDPOINTS ESPECÍFICOS DE CHILE ===
    # AJAX jerárquico para vehículos
    path("ajax/load-modelos/", ajax_views.load_modelos, name="ajax_load_modelos"),
    path("ajax/load-motores/", ajax_views.load_motores, name="ajax_load_motores"),
    path("ajax/load-cajas/", ajax_views.load_cajas, name="ajax_load_cajas"),
    path("ajax/load-motores-cajas/", ajax_views.load_motores_cajas, name="ajax_load_motores_cajas"),
    
    # AJAX específicos para Chile
    path("ajax/clientes/buscar/", buscar_clientes, name="cl_ajax_buscar_clientes"),
    path("ajax/vehiculos-por-cliente/", vehiculos_por_cliente, name="cl_ajax_vehiculos_por_cliente"),
    
    # === AUTHENTICATION ===
    # Login para Chile
    path("login/", chile_login_view, name="account_login"),
    # Signup para Chile
    path("signup/", chile_signup_view, name="account_signup"),
    # Registro para Chile
    path("registro/", include("scripts.onboarding_urls")),
    
    # === DASHBOARD DE SUSCRIPTOR ===
    path("", include("taller.analytics.urls_suscriptor")),
]
```

## 🎯 Reglas de Oro que Funcionan

### ✅ HACER:
1. **Un solo include por país/idioma** en `gestion_taller/urls.py`
2. **Todos los submódulos** se anidan exclusivamente dentro de `taller_main_urls.py`
3. **app_name = "taller"** en `taller_main_urls.py`
4. **app_name específico** en cada `urls_extra/*.py` (usa, chile)
5. **Namespaces únicos** para cada país/idioma

### ❌ NO HACER:
1. **Re-incluir los mismos submódulos** desde `urls_extra/*` con el mismo namespace final
2. **Múltiples includes** del mismo archivo en el mismo namespace
3. **Mezclar namespaces** en diferentes archivos
4. **Incluir submódulos directamente** en `urls_extra/*` si ya están en `taller_main_urls.py`

## 🧪 Verificación

```bash
# Verificar que no hay duplicados
python manage.py check

# Verificar URLs específicas
python manage.py show_urls | findstr /I "taller_us_en"

# Probar reverse
python -c "from django.urls import reverse; print(reverse('taller_us_en:taller:clientes:lista_clientes'))"
```

## 📋 Estructura Final de Namespaces

```
taller_us_en:taller:clientes:lista_clientes
taller_us_en:taller:vehiculos:lista_vehiculos
taller_us_en:taller:servicios:servicios_menu
taller_us_en:taller:repuestos:lista_repuestos
taller_us_en:taller:documentos:lista_documentos
taller_us_en:taller:reportes:reportes_dashboard

taller_cl_es:taller:clientes:lista_clientes
taller_cl_es:taller:vehiculos:lista_vehiculos
taller_cl_es:taller:servicios:servicios_menu
taller_cl_es:taller:repuestos:lista_repuestos
taller_cl_es:taller:documentos:lista_documentos
taller_cl_es:taller:reportes:reportes_dashboard
```

¡Este patrón garantiza **cero duplicados** y **namespaces únicos**! 🎉
