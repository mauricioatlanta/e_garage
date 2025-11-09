# Estructura de URLs por País - eGarage

## 📋 Resumen de la Estructura

Este documento explica la estructura de URLs implementada para los mercados de Chile y USA en eGarage.

## 🌍 URLs Principales

### 1. **Página de Inicio - Selector de País**
- **URL**: `http://127.0.0.1:8000/`
- **Template**: `templates/public/selector_pais.html`
- **Descripción**: Página de bienvenida que permite al usuario escoger su país (Chile 🇨🇱 o USA 🇺🇸)
- **Características**:
  - Diseño futurista con animaciones
  - Sin opciones de login/registro (solo selector de país)
  - Redirige a `/cl/` o `/us/` según selección

### 2. **Landing Page Chile**
- **URL**: `http://127.0.0.1:8000/cl/`
- **Template**: `templates/public/landing_chile_with_header.html`
- **Idioma**: Español 100%
- **Características**:
  - Header con logo y opciones de navegación
  - Botones de "Iniciar Sesión" y "Registrarse" en el header
  - Contenido en español orientado al mercado chileno
  - Sección de funcionalidades
  - Call-to-action para registro
  - Precios en CLP
  - IVA chileno

### 3. **Landing Page USA**
- **URL**: `http://127.0.0.1:8000/us/`
- **Template**: `templates/us/en/landing_usa.html`
- **Vista**: `taller/views_extra/bienvenida_usa.py`
- **Idioma**: Inglés 100% (con opción para español futuro)
- **Características**:
  - Header con logo y opciones de navegación
  - Botones de "Sign In" y "Register" en el header
  - Contenido en inglés orientado al mercado estadounidense
  - Sección de funcionalidades (Features)
  - Planes de precios (Pricing)
  - Testimonios
  - FAQs
  - Precios en USD
  - Sales Tax USA

## 📁 Estructura de Archivos

```
e_garage/
├── templates/
│   ├── public/
│   │   ├── selector_pais.html              # Selector de país (/)
│   │   ├── landing_chile_with_header.html  # Landing Chile (/cl/)
│   │   └── landing_chile.html              # Landing Chile antigua (sin header)
│   ├── us/
│   │   └── en/
│   │       └── landing_usa.html            # Landing USA (/us/)
│   └── ...
├── taller/
│   ├── views_extra/
│   │   └── bienvenida_usa.py               # Vista para /us/
│   └── urls_extra/
│       ├── chile.py                        # URLs para /cl/es/
│       └── usa.py                          # URLs para /us/
└── gestion_taller/
    └── urls.py                             # URLs principales del proyecto
```

## 🔧 Configuración Implementada

### Cambios en `gestion_taller/urls.py`

1. **Raíz del sitio (`/`)**:
   ```python
   path("", TemplateView.as_view(template_name="public/selector_pais.html"), name="home")
   ```

2. **Landing Chile (`/cl/`)**:
   ```python
   path("cl/", TemplateView.as_view(template_name="public/landing_chile_with_header.html"), name="cl_home_welcome")
   ```

3. **Landing USA (`/us/`)**:
   - Usa `include` para `taller.urls_extra.usa`
   - La raíz de `/us/` llama a la vista `bienvenida_usa`

### Cambios en `taller/views_extra/bienvenida_usa.py`

La vista ahora renderiza la landing page con header:
```python
def bienvenida_usa(request):
    translation.activate("en")
    request.LANGUAGE_CODE = "en"

    context = {
        'LANGUAGE_CODE': 'en',
        'page_title': 'eGarage USA - Professional Automotive Management',
        'is_usa_market': True,
    }

    return render(request, "us/en/landing_usa.html", context)
```

## 🎨 Características de las Templates

### Selector de País (`selector_pais.html`)
- Fondo oscuro futurista con partículas animadas
- Logo con efecto de pulso
- Dos botones grandes para Chile y USA
- Animación de entrada suave
- 100% responsive

### Landing Chile (`landing_chile_with_header.html`)
- **Header fijo** con:
  - Logo y nombre de la marca
  - Badge de país (🇨🇱 Chile)
  - Links de navegación (Funcionalidades, Precios)
  - Botón "Iniciar Sesión"
  - Botón "Registrarse"

- **Hero Section** con:
  - Badge de sistema funcional
  - Título grande
  - Descripción del servicio
  - Tres botones de acción (Comenzar, Iniciar Sesión, Ver Funcionalidades)
  - Lista de beneficios

- **Sección de Funcionalidades** con 6 cards:
  - Gestión de Vehículos
  - CRM de Clientes
  - Inventario de Repuestos
  - Facturación e IVA
  - Analytics y KPIs
  - Listo para Móviles

- **CTA Final** con botones de registro
- **Footer** simple

### Landing USA (`landing_usa.html`)
- **Header fijo** con:
  - Logo con efecto de brillo
  - Badge de país (🇺🇸 United States)
  - Links de navegación (Pricing, Features)
  - Botón "Sign In"

- **Hero Section** animado con:
  - Fondo con gradientes y partículas
  - Badge de sistema funcional
  - Título con gradiente
  - Tres botones de acción
  - Lista de beneficios
  - Imagen de preview

- **Features Section** con 6 cards
- **Pricing Section** con 3 planes (Starter, Semiannual, Annual)
- **Testimonios** de clientes USA
- **FAQs** con CTA final
- **Animaciones** y efectos hover

## 🔐 Acceso a Login/Registro

### Desde las Landing Pages:

**Chile (`/cl/`):**
- Header → "Iniciar Sesión" → `/accounts/login/`
- Header → "Registrarse" → `/accounts/signup/`
- Hero → "Comenzar Ahora" → `/accounts/signup/`
- Hero → "Iniciar Sesión" → `/accounts/login/`

**USA (`/us/`):**
- Header → "Sign In" → `/accounts/login/`
- Hero → "Sign In" → `/accounts/login/`
- Pricing → "Start now" / "Choose Plan" → `/accounts/register/`
- CTA → "Get Started Now" → `/accounts/register/`

## 🚀 Testing

Para probar la nueva estructura:

1. **Selector de País**:
   ```
   http://127.0.0.1:8000/
   ```

2. **Landing Chile**:
   ```
   http://127.0.0.1:8000/cl/
   ```

3. **Landing USA**:
   ```
   http://127.0.0.1:8000/us/
   ```

## 📱 Responsive Design

Todas las templates son 100% responsive:
- Mobile first design
- Breakpoints en 768px y 1024px
- Navegación adaptable
- Botones optimizados para touch
- Imágenes y videos optimizados

## 🎯 Flujo del Usuario

```
Usuario accede a 127.0.0.1:8000
    ↓
Selector de País
    ↓
┌────────────────┬────────────────┐
│ Selecciona CL  │ Selecciona US  │
│       ↓        │       ↓        │
│  Landing Chile │  Landing USA   │
│  (con header)  │  (con header)  │
│       ↓        │       ↓        │
│  Botones de    │  Botones de    │
│  Login/Signup  │  Login/Signup  │
│       ↓        │       ↓        │
└────────────────┴────────────────┘
           ↓
    Sistema eGarage
```

## 📝 Notas Importantes

1. **Selector de País sin Login**: La página raíz (`/`) NO tiene opciones de login/registro, solo permite seleccionar el país.

2. **Landing Pages con Header**: Tanto `/cl/` como `/us/` tienen headers completos con opciones de login y registro.

3. **Idiomas**:
   - Chile: 100% español (sin opción de cambio)
   - USA: 100% inglés (con posibilidad de agregar español futuro)

4. **URLs de Autenticación**:
   - Login: `/accounts/login/`
   - Registro: `/accounts/signup/`
   - Estas URLs son globales y funcionan desde ambos países

5. **Después del Login**: Los usuarios son redirigidos según su país configurado en su empresa.

## 🔄 Futuras Mejoras

- [ ] Agregar opción de cambio de idioma en USA (inglés/español)
- [ ] Personalizar páginas de login por país
- [ ] Agregar más países (México, Argentina, etc.)
- [ ] A/B testing de conversión en landing pages
- [ ] Analytics de qué país genera más registros

---

**Última actualización**: 26 de octubre de 2025
**Autor**: Sistema de Gestión eGarage
