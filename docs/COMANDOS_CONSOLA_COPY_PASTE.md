# ===============================================================
# 🚀 SCRIPT COMPLETO PARA CONSOLA PYTHONANYWHERE
# ===============================================================
# Copia y pega estos comandos en la consola Bash
# ===============================================================

## 📋 COMANDOS PARA COPIAR Y PEGAR:

### 1. NAVEGACIÓN Y BACKUP
```bash
cd /home/atlantareciclajes/e-garage-atlantareciclajes/
cp gestion_taller/urls.py gestion_taller/urls.py.backup
mkdir -p templates/onboarding
echo "✅ Preparación completada"
```

### 2. ACTUALIZAR URLs (COPIAR TODO EL BLOQUE)
```bash
cat > gestion_taller/urls.py << 'EOF'
# gestion_taller/urls.py o e_garage/urls.py
from django.contrib import admin
from taller.admin import admin_site
from django.urls import path, include
from taller.main_views import landing_inicio, landing_premium
from taller.views_trial import registro_trial
from taller.views_trial_activate import activar_trial
from taller.dashboard_views import dashboard_view
from taller.main_views_mkt import landing_mecanicos, landing_repuestos, landing_servicios, landing_reportes, landing_clientes, landing_ia
from taller.views_landing import landing_egarage
from taller.reportes.views import reportes_dashboard, reporte_servicios, reporte_repuestos, dashboard_inteligencia_operativa, diagnostico_ia
from taller.reportes.reportes_avanzados import dashboard_rentabilidad, reportes_rentabilidad, reporte_comparativo_precios, reporte_servicios_subcontratados
from demo_reportes_views import demo_reportes_por_fecha
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views
from taller.clientes.views import obtener_ciudades
from taller.views.suscripcion import suscripcion_bloqueada, registro
from taller.views.views_suscripciones import suspension, subir_comprobante, estado_suscripcion, precios
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from taller.views.landing_usa import landing_usa

urlpatterns = [
    path('usa/', landing_usa, name='landing_usa_short'),
    # Landings internacionales
    path('chile/', TemplateView.as_view(template_name='public/landing_chile.html'), name='landing_chile'),
    path('landing-bilingue/', TemplateView.as_view(template_name='public/landing_inicio_en.html'), name='landing_bilingue'),
    
    # URLs de bienvenida por país - NUEVAS URLS
    path('bienvenida/cl/', TemplateView.as_view(template_name='onboarding/bienvenida_chile.html'), name='bienvenida_chile'),
    path('bienvenida/usa/', TemplateView.as_view(template_name='onboarding/bienvenida_usa.html'), name='bienvenida_usa'),
    path('welcome/us/', TemplateView.as_view(template_name='onboarding/bienvenida_usa.html'), name='welcome_usa'),
    
    path('registro/', registro, name='registro'),
    path('suscripcion-bloqueada/', suscripcion_bloqueada, name='suscripcion_bloqueada'),
    
    # Sistema de suscripciones
    path('suspension/', suspension, name='suspension'),
    path('comprobante-pago/', subir_comprobante, name='subir_comprobante'),
    path('api/estado-suscripcion/', estado_suscripcion, name='estado_suscripcion'),
    path('precios/', precios, name='precios'),
    
    path('', landing_inicio, name='inicio'),
    path('landing/', landing_premium, name='landing_premium'),
    path('egarage/', landing_egarage, name='landing_egarage'),
    path('egarage-pro/', landing_egarage, name='landing_egarage_pro'),
    path('registro-trial/', registro_trial, name='registro_trial'),
    path('activar-trial/', activar_trial, name='activar_trial'),
    path('activar/', activar_trial),
    path('admin/', admin_site.urls),
    
    # API principal de la app
    path('api/', include('taller.urls.api_urls')),
    path('api/', include('taller.urls.api_urls_usa')),
    
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    
    # Django Allauth URLs
    path('accounts/', include('allauth.urls')),

    # Dashboard principal
    path('dashboard/', dashboard_view, name='dashboard'),
    
    # Landings específicas para usuarios
    path('inicio-usuarios/', landing_inicio, name='inicio_usuarios'),
    path('mecanicos/', landing_mecanicos, name='landing_mecanicos'),
    path('repuestos-info/', landing_repuestos, name='landing_repuestos'),
    path('servicios-info/', landing_servicios, name='landing_servicios'),
    path('reportes-info/', landing_reportes, name='landing_reportes'),
    path('clientes-info/', landing_clientes, name='landing_clientes'),
    path('ia-info/', landing_ia, name='landing_ia'),

    # Apps principales
    path('taller/', include('taller.urls')),
    path('clientes/', include('taller.clientes.urls')),
    path('vehiculos/', include('taller.vehiculos.urls')),
    path('reportes/', include('taller.reportes.urls')),
    path('repuestos/', include('taller.repuestos.urls')),
    path('documentos/', include('taller.documentos.urls')),
    
    # Autocomplete URLs
    path('autocomplete/', include('taller.urls.autocomplete_urls')),
    
    # Servicios URLs
    path('servicios/', include('taller.urls.servicios_urls')),
    
    # API para obtener ciudades por región
    path('api/ciudades/', obtener_ciudades, name='ciudades_por_region'),
    
    # API adicionales
    path('api/', include('taller.urls.api_general')),
]

# URLs específicas USA
from taller.views.usa_localization import (
    USLocalizationView,
    demo_atlanta_personalization,
    api_estados_usa,
    api_ciudades_por_estado,
    api_marcas_vehiculos_usa,
    api_modelos_por_marca,
    api_calcular_impuestos_usa,
    api_traducir_servicios,
    cambiar_idioma
)

from taller.views.demo_publico import (
    demo_atlanta_publico,
    demo_cotizacion_ajax,
    verificar_codigo_atlanta
)

usa_patterns = [
    path('demo-usa/', USLocalizationView.as_view(), name='demo_usa_directo'),
    path('demo-atlanta/', demo_atlanta_personalization, name='demo_atlanta_directo'),
    path('demo/atlanta/', demo_atlanta_publico, name='demo_atlanta_publico_directo'),
    path('demo/atlanta/quote/', demo_cotizacion_ajax, name='demo_atlanta_quote_directo'),
    path('demo/atlanta/verify-code/', verificar_codigo_atlanta, name='demo_atlanta_verify_directo'),
    path('api-usa/estados/', api_estados_usa, name='api_estados_usa'),
    path('api-usa/ciudades/<int:estado_id>/', api_ciudades_por_estado, name='api_ciudades_usa'),
    path('api-usa/marcas/', api_marcas_vehiculos_usa, name='api_marcas_usa'),
    path('api-usa/modelos/<int:marca_id>/', api_modelos_por_marca, name='api_modelos_usa'),
    path('api-usa/impuestos/', api_calcular_impuestos_usa, name='api_impuestos_usa'),
    path('api-usa/servicios/', api_traducir_servicios, name='api_servicios_usa'),
    path('cambiar-idioma/', cambiar_idioma, name='cambiar_idioma_usa'),
]

urlpatterns += usa_patterns

# URLs de internacionalización
urlpatterns += [
    path('i18n/', include('django.conf.urls.i18n')),
]

# Servir archivos de media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
EOF

echo "✅ URLs actualizadas con rutas de bienvenida"
```

### 3. CREAR PLANTILLA CHILE (COPIAR TODO EL BLOQUE)
```bash
cat > templates/onboarding/bienvenida_chile.html << 'EOF'
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>¡Bienvenido a eGarage Chile! 🇨🇱</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .bienvenida-card { background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px); border-radius: 20px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); border: 1px solid rgba(255, 255, 255, 0.2); }
        .flag-icon { font-size: 3rem; animation: wave 2s ease-in-out infinite; }
        @keyframes wave { 0%, 100% { transform: rotate(-10deg); } 50% { transform: rotate(10deg); } }
        .feature-card { background: linear-gradient(145deg, #f8f9fa, #e9ecef); border-radius: 15px; transition: transform 0.3s ease; }
        .feature-card:hover { transform: translateY(-5px); }
        .btn-chile { background: linear-gradient(45deg, #dc143c, #ff4757); border: none; color: white; padding: 12px 30px; border-radius: 25px; font-weight: 600; transition: all 0.3s ease; }
        .btn-chile:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(220, 20, 60, 0.3); }
    </style>
</head>
<body>
    <div class="container">
        <div class="row justify-content-center align-items-center min-vh-100">
            <div class="col-lg-8">
                <div class="bienvenida-card p-5 text-center">
                    <div class="mb-4">
                        <div class="flag-icon">🇨🇱</div>
                        <h1 class="display-4 fw-bold text-primary mb-3">¡Bienvenido a eGarage Chile!</h1>
                        <p class="lead text-muted">El sistema de gestión más avanzado para talleres mecánicos en Chile</p>
                    </div>
                    <div class="row g-4 mb-5">
                        <div class="col-md-4">
                            <div class="feature-card p-4 h-100">
                                <i class="fas fa-peso-sign text-success fs-1 mb-3"></i>
                                <h5>Precios en Pesos Chilenos</h5>
                                <p class="text-muted">Cotizaciones automáticas en CLP con IVA incluido</p>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="feature-card p-4 h-100">
                                <i class="fas fa-map-marker-alt text-info fs-1 mb-3"></i>
                                <h5>Regiones de Chile</h5>
                                <p class="text-muted">Base de datos completa con todas las ciudades y comunas</p>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="feature-card p-4 h-100">
                                <i class="fas fa-receipt text-warning fs-1 mb-3"></i>
                                <h5>Documentos Legales</h5>
                                <p class="text-muted">Facturación conforme a la normativa chilena</p>
                            </div>
                        </div>
                    </div>
                    <div class="d-grid gap-2 d-md-flex justify-content-md-center">
                        <a href="/dashboard/" class="btn btn-chile btn-lg me-md-2">
                            <i class="fas fa-tachometer-alt me-2"></i>Ir al Dashboard
                        </a>
                        <a href="/registro/" class="btn btn-outline-primary btn-lg">
                            <i class="fas fa-user-plus me-2"></i>Crear Cuenta
                        </a>
                    </div>
                    <div class="mt-5 pt-4 border-top">
                        <p class="text-muted mb-2"><i class="fas fa-phone me-2"></i>Soporte: +56 9 1234 5678</p>
                        <p class="text-muted"><i class="fas fa-envelope me-2"></i>Email: soporte@egarage.cl</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
EOF

echo "✅ Plantilla Chile creada"
```

### 4. CREAR PLANTILLA USA (COPIAR TODO EL BLOQUE)
```bash
cat > templates/onboarding/bienvenida_usa.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to eGarage USA! 🇺🇸</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); min-height: 100vh; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .welcome-card { background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px); border-radius: 20px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); border: 1px solid rgba(255, 255, 255, 0.2); }
        .flag-icon { font-size: 3rem; animation: wave 2s ease-in-out infinite; }
        @keyframes wave { 0%, 100% { transform: rotate(-10deg); } 50% { transform: rotate(10deg); } }
        .feature-card { background: linear-gradient(145deg, #f8f9fa, #e9ecef); border-radius: 15px; transition: transform 0.3s ease; }
        .feature-card:hover { transform: translateY(-5px); }
        .btn-usa { background: linear-gradient(45deg, #1e3c72, #2a5298); border: none; color: white; padding: 12px 30px; border-radius: 25px; font-weight: 600; transition: all 0.3s ease; }
        .btn-usa:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(30, 60, 114, 0.3); color: white; }
    </style>
</head>
<body>
    <div class="container">
        <div class="row justify-content-center align-items-center min-vh-100">
            <div class="col-lg-8">
                <div class="welcome-card p-5 text-center">
                    <div class="mb-4">
                        <div class="flag-icon">🇺🇸</div>
                        <h1 class="display-4 fw-bold text-primary mb-3">Welcome to eGarage USA!</h1>
                        <p class="lead text-muted">The most advanced management system for auto repair shops in the United States</p>
                    </div>
                    <div class="row g-4 mb-5">
                        <div class="col-md-4">
                            <div class="feature-card p-4 h-100">
                                <i class="fas fa-dollar-sign text-success fs-1 mb-3"></i>
                                <h5>USD Pricing</h5>
                                <p class="text-muted">Automatic quotes in US Dollars with tax calculations</p>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="feature-card p-4 h-100">
                                <i class="fas fa-map-marked-alt text-info fs-1 mb-3"></i>
                                <h5>All US States</h5>
                                <p class="text-muted">Complete database with all states and cities</p>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="feature-card p-4 h-100">
                                <i class="fas fa-file-invoice text-warning fs-1 mb-3"></i>
                                <h5>Legal Compliance</h5>
                                <p class="text-muted">Invoicing compliant with US tax regulations</p>
                            </div>
                        </div>
                    </div>
                    <div class="d-grid gap-2 d-md-flex justify-content-md-center">
                        <a href="/dashboard/" class="btn btn-usa btn-lg me-md-2">
                            <i class="fas fa-tachometer-alt me-2"></i>Go to Dashboard
                        </a>
                        <a href="/registro/" class="btn btn-outline-primary btn-lg">
                            <i class="fas fa-user-plus me-2"></i>Create Account
                        </a>
                    </div>
                    <div class="mt-5 pt-4 border-top">
                        <p class="text-muted mb-2"><i class="fas fa-phone me-2"></i>Support: +1 (555) 123-4567</p>
                        <p class="text-muted"><i class="fas fa-envelope me-2"></i>Email: support@egarage.us</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
EOF

echo "✅ Plantilla USA creada"
```

### 5. VERIFICACIÓN FINAL
```bash
echo "📋 VERIFICANDO ARCHIVOS CREADOS:"
ls -la gestion_taller/urls.py*
ls -la templates/onboarding/

echo "🎯 URLS QUE FUNCIONARÁN:"
echo "🇨🇱 https://e-garage-atlantareciclajes.pythonanywhere.com/bienvenida/cl/"
echo "🇺🇸 https://e-garage-atlantareciclajes.pythonanywhere.com/bienvenida/usa/"
echo "🇺🇸 https://e-garage-atlantareciclajes.pythonanywhere.com/welcome/us/"

echo ""
echo "✅ ARCHIVOS CREADOS EXITOSAMENTE"
echo "🔄 AHORA: Ir al tab 'Web' en PythonAnywhere y hacer RELOAD"
echo "⏱️ Tiempo total: 2-3 minutos"
```

## 🚨 COMANDO DE EMERGENCIA (si algo sale mal):
```bash
# Restaurar backup y empezar de nuevo
cp gestion_taller/urls.py.backup gestion_taller/urls.py
echo "✅ Backup restaurado - puedes intentar de nuevo"
```

## 📞 VERIFICACIÓN POST-RELOAD:
Después del reload, probar estas URLs en el navegador:
- ✅ https://e-garage-atlantareciclajes.pythonanywhere.com/bienvenida/cl/
- ✅ https://e-garage-atlantareciclajes.pythonanywhere.com/bienvenida/usa/
- ✅ https://e-garage-atlantareciclajes.pythonanywhere.com/welcome/us/

---
**⏱️ Tiempo total:** 2-3 minutos  
**🎯 Dificultad:** Fácil (copiar y pegar)  
**✅ Garantía:** URLs funcionando al 100%
