# ANÁLISIS DE INTERNACIONALIZACIÓN (i18n) - TEMPLATES E_GARAGE

**Fecha:** 27 de Octubre, 2025
**Contexto:** E_garage es una aplicación de suscripción para mercado chileno (español) y estadounidense (inglés/español)

---

## ESTRATEGIA DE INTERNACIONALIZACIÓN

E_garage utiliza una **estrategia híbrida** de internacionalización:

1. **Templates comunes** con tags i18n de Django (`{% trans %}`, `{% blocktrans %}`)
2. **Templates específicas por país/idioma** para diferencias significativas en UX
3. **Middleware de país** (`EmpresaMiddleware`, `SimpleCountryRedirectMiddleware`)
4. **Middleware de idioma** (`LanguagePolicyMiddleware`) para decisión final de idioma

---

## ESTRUCTURA DE DIRECTORIOS POR PAÍS/IDIOMA

### Patrón de Rutas

```
templates/
├── cl/                    # Chile
│   ├── es/               # Español (principal)
│   │   ├── clientes/     # 9 archivos
│   │   └── dashboard/    # 1 archivo
│   ├── en/               # Inglés (soporte limitado)
│   │   └── dashboard/    # 1 archivo
│   └── dashboard_chile.html
│
├── us/                    # Estados Unidos
│   ├── en/               # Inglés (principal)
│   │   └── clientes/     # 5 archivos
│   ├── es/               # Español (población hispana)
│   │   └── clientes/     # 5 archivos
│   ├── centro_operaciones_espacial.html
│   └── dashboard_usa.html
│
└── taller/                # Módulo principal
    ├── common/           # Templates comunes multiidioma (20 archivos)
    ├── cl/              # Chile específico
    │   └── es/
    │       ├── dashboard/   # 1 archivo
    │       ├── vehiculos/   # 1 archivo
    │       └── account/     # 1 archivo
    └── us/              # USA específico (19 archivos)
        ├── en/
        │   ├── vehiculos/   # 8 archivos
        │   ├── servicios/   # 3 archivos
        │   ├── clientes/    # 2 archivos
        │   ├── dashboard/   # 1 archivo
        │   └── account/     # 1 archivo
        └── es/
            ├── vehiculos/   # 1 archivo
            ├── servicios/   # 1 archivo
            └── clientes/    # 1 archivo
```

---

## DESGLOSE POR PAÍS E IDIOMA

### 1. CHILE (CL)

#### Idioma Principal: Español (es)

**Ubicaciones:**
- `templates/cl/es/clientes/` - 9 archivos
  - Lista y gestión de clientes en español chileno
- `templates/cl/es/dashboard/` - 1 archivo
  - Dashboard específico Chile
- `templates/cl/es/taller/` - Varios subdirectorios
  - Templates de taller adaptadas a mercado chileno
- `templates/cl/dashboard_chile.html`
- `templates/taller/cl/es/dashboard/` - 1 archivo
- `templates/taller/cl/es/vehiculos/` - 1 archivo
- `templates/taller/cl/es/account/` - 1 archivo

**Total estimado:** ~15 archivos específicos Chile español

**Características distintivas:**
- Terminología local (ej: "RUT" en vez de "Tax ID")
- Formato de moneda: Peso chileno ($)
- Formato de fecha: DD/MM/YYYY
- Regiones y comunas chilenas

#### Idioma Secundario: Inglés (en) - Soporte Limitado

**Ubicaciones:**
- `templates/cl/en/dashboard/` - 1 archivo
- `templates/cl/en/taller/` - Posibles templates adicionales

**Total estimado:** ~2-3 archivos Chile inglés

**Propósito:** Soporte para usuarios internacionales operando en Chile

---

### 2. ESTADOS UNIDOS (US)

#### Idioma Principal: Inglés (en)

**Ubicaciones:**
- `templates/us/en/clientes/` - 5 archivos
  - Customer management en inglés americano
- `templates/us/en/landing_usa.html`
- `templates/taller/us/en/vehiculos/` - 8 archivos
  - Vehicle management (VIN, MPG, etc.)
- `templates/taller/us/en/servicios/` - 3 archivos
  - Service management
- `templates/taller/us/en/clientes/` - 2 archivos
- `templates/taller/us/en/dashboard/` - 1 archivo
- `templates/taller/us/en/account/` - 1 archivo

**Total:** ~19 archivos USA inglés

**Características distintivas:**
- Terminología americana (ej: "ZIP Code", "State")
- Formato de moneda: Dólar americano ($)
- Formato de fecha: MM/DD/YYYY
- Estados y códigos postales USA
- Unidades imperiales (miles, gallons)

#### Idioma Secundario: Español (es) - Población Hispana

**Ubicaciones:**
- `templates/us/es/clientes/` - 5 archivos
  - Gestión de clientes en español para mercado hispano USA
- `templates/taller/us/es/vehiculos/` - 1 archivo
- `templates/taller/us/es/servicios/` - 1 archivo
- `templates/taller/us/es/clientes/` - 1 archivo

**Total:** ~8 archivos USA español

**Propósito:** Atender a población hispana en Estados Unidos

**Características distintivas:**
- Español neutro/americano (no chileno)
- Mantiene formatos USA (fechas, unidades)
- Moneda en dólares pero etiquetas en español

---

### 3. TEMPLATES COMUNES (Multiidioma)

#### `templates/taller/common/` (20 archivos)

**Archivos principales:**
- `documentos/` - 6 archivos
  - Templates de facturas/órdenes que usan tags i18n
- `clientes/` - 4 archivos
  - Componentes de clientes reutilizables
- `servicios/` - 2 archivos
- `dashboard/` - 2 archivos
  - `centro_operaciones_espacial.html` (dashboard futurista común)
- `vehiculos/` - 1 archivo
- `repuestos/` - 1 archivo
- Otros componentes base

**Estrategia:**
- Usan `{% load i18n %}`
- Tags `{% trans "texto" %}` para cadenas simples
- Tags `{% blocktrans %}...{% endblocktrans %}` para bloques
- Se adaptan automáticamente según `LANGUAGE_CODE` activo

**Ejemplo de uso:**
```django
{% load i18n %}
<h1>{% trans "Customers" %}</h1>
<p>{% blocktrans %}Welcome to the customer management system{% endblocktrans %}</p>
```

#### `templates/common/` (4 archivos)

- `_footer_company.html`
- `base.html`
- `components/tabla_otro_servicio.html`
- `dashboard/centro_operaciones_espacial.html`

**Uso:** Templates base compartidas entre países

---

## CONFIGURACIÓN DE IDIOMA

### `settings.py`

```python
LANGUAGE_CODE = "es"  # fallback global
LANGUAGES = [("en", "English"), ("es", "Español")]
LOCALE_PATHS = [BASE_DIR / "locale"]
USE_I18N = True
```

### Middleware Stack (orden)

1. `EmpresaMiddleware` - Detecta país de la empresa del usuario
2. `SimpleCountryRedirectMiddleware` - Redirige según país
3. `LanguagePolicyMiddleware` - Decide idioma final basado en:
   - País de la empresa
   - Preferencia de usuario
   - Header `Accept-Language`

---

## ARCHIVOS DE TRADUCCIÓN

### Estructura esperada:

```
locale/
├── en/
│   └── LC_MESSAGES/
│       ├── django.po    # Traducciones inglés
│       └── django.mo    # Compilado
└── es/
    └── LC_MESSAGES/
        ├── django.po    # Traducciones español
        └── django.mo    # Compilado
```

**Estado actual:** Carpetas existen con archivos .po y .mo

---

## ANÁLISIS DE COBERTURA

### Módulos con Buena Cobertura i18n:

✅ **Vehículos (vehicles):**
- `taller/us/en/vehiculos/` - 8 archivos
- `taller/us/es/vehiculos/` - 1 archivo
- `taller/cl/es/vehiculos/` - 1 archivo
- `taller/common/vehiculos/` - 1 archivo (común)

✅ **Clientes (customers):**
- `cl/es/clientes/` - 9 archivos
- `us/en/clientes/` - 5 archivos
- `us/es/clientes/` - 5 archivos
- `taller/common/clientes/` - 4 archivos (común)

✅ **Servicios (services):**
- `taller/us/en/servicios/` - 3 archivos
- `taller/us/es/servicios/` - 1 archivo
- `taller/common/servicios/` - 2 archivos (común)

### Módulos con Cobertura Limitada:

⚠️ **Repuestos (parts):**
- `taller/repuestos/` - 22 archivos (¿sin versiones país-específicas?)
- `taller/common/repuestos/` - 1 archivo

⚠️ **Reportes:**
- `taller/reportes/` - 15 archivos (¿mayormente español?)
- `taller/templates/taller/reportes/` - 6 archivos

⚠️ **Documentos:**
- `taller/documentos/` - 25 archivos
  - `documentos/us/en/` - 6 archivos
  - `documentos/us/es/` - 2 archivos
  - `documentos/cl/es/` - 2 archivos
  - `documentos/common/` - 1 archivo
  - Resto sin clasificar por país

---

## PATRONES DETECTADOS

### Patrón 1: Templates Separadas por País/Idioma

**Uso:** Cuando hay diferencias significativas en UX o contenido

**Ventajas:**
- Total control sobre diseño específico
- Fácil personalizar por mercado
- No hay condicionales complejos en templates

**Desventajas:**
- Duplicación de código
- Mantenimiento múltiple
- Inconsistencias potenciales

**Ejemplo:**
```
taller/us/en/vehiculos/crear_vehiculo.html  (inglés USA)
taller/cl/es/vehiculos/crear_vehiculo.html  (español Chile)
```

### Patrón 2: Templates Comunes con i18n Tags

**Uso:** Cuando solo cambian textos pero no estructura

**Ventajas:**
- Un solo archivo para mantener
- Consistencia garantizada
- Fácil agregar idiomas

**Desventajas:**
- Menos flexible para diferencias regionales
- Puede ser complejo con mucho contenido

**Ejemplo:**
```django
<!-- taller/common/clientes/lista_clientes.html -->
{% load i18n %}
<h1>{% trans "Customers" %}</h1>
<button>{% trans "Add Customer" %}</button>
```

### Patrón 3: Híbrido (Base Común + Extensiones País-Específicas)

**Uso:** Template base común, bloques sobrescritos por país

**Ventajas:**
- Balance entre reutilización y personalización
- Sigue patrón Django de herencia
- Mantenible

**Desventajas:**
- Requiere planificación de bloques
- Curva de aprendizaje

**Ejemplo:**
```django
<!-- taller/common/vehiculos/base_vehiculo.html -->
{% block vehicle_id_label %}
  {% trans "Vehicle ID" %}
{% endblock %}

<!-- taller/cl/es/vehiculos/detalle.html -->
{% extends "taller/common/vehiculos/base_vehiculo.html" %}
{% block vehicle_id_label %}
  Patente (RUT del Vehículo)
{% endblock %}
```

---

## RECOMENDACIONES

### 1. Auditar Uso de Templates

**Acción:** Identificar qué templates específicas por país son realmente necesarias

**Criterios para templates separadas:**
- Formato de datos diferente (fechas, moneda)
- Terminología técnica diferente (patente vs license plate)
- Requisitos legales diferentes
- UX significativamente distinta

**Criterios para templates comunes con i18n:**
- Solo cambian textos
- Misma estructura y flujo
- No hay diferencias regionales importantes

### 2. Consolidar Módulos con Baja Diferenciación

**Candidatos para consolidación:**
- `taller/repuestos/` - Unificar en `taller/common/repuestos/` con i18n
- Algunos reportes que solo cambian idioma
- Dashboards similares entre países

### 3. Mejorar Cobertura USA Español

**Observación:** USA tiene buena cobertura en inglés (19 archivos) pero limitada en español (8 archivos)

**Acción recomendada:**
- Revisar qué módulos faltan en `taller/us/es/`
- Priorizar según población hispana esperada
- Considerar traducciones automáticas de `us/en/` → `us/es/`

### 4. Documentar Estrategia de Selección

**Crear guía:** `docs/I18N_STRATEGY.md`

**Contenido sugerido:**
- Cuándo crear template específica por país
- Cuándo usar template común con i18n
- Nomenclatura de archivos
- Bloques estándar para sobrescribir
- Proceso de traducción

### 5. Implementar Tests de Cobertura i18n

**Objetivo:** Garantizar que todas las vistas tienen template para cada idioma soportado

**Herramienta sugerida:**
```python
# tests/test_i18n_coverage.py
def test_all_views_have_translations():
    """Verifica que cada vista tenga template en es y en"""
    for url_pattern in get_all_url_patterns():
        for lang in ['en', 'es']:
            with override_language(lang):
                response = client.get(url_pattern)
                assert response.status_code == 200
```

### 6. Optimizar Estructura de Directorios

**Propuesta:** Reorganizar para claridad

**Estructura sugerida:**
```
templates/
├── common/              # Multiidioma con i18n tags
│   ├── base/
│   ├── components/
│   └── layouts/
│
├── country/             # Templates específicas por país
│   ├── cl/
│   │   ├── es/         # Principal
│   │   └── en/         # Secundario
│   └── us/
│       ├── en/         # Principal
│       └── es/         # Secundario
│
├── public/              # Landing, sin autenticación
├── account/             # Autenticación (común)
├── admin/               # Administración (común)
└── emails/              # Templates de email (con i18n)
```

---

## HERRAMIENTAS ÚTILES

### Listar templates por idioma:
```powershell
# Templates Chile español
Get-ChildItem -Path "templates\cl\es" -Filter "*.html" -Recurse

# Templates USA inglés
Get-ChildItem -Path "templates\us\en" -Filter "*.html" -Recurse
```

### Buscar templates sin i18n:
```powershell
# Buscar archivos en common/ sin {% load i18n %}
Get-ChildItem -Path "templates\taller\common" -Filter "*.html" -Recurse |
    Where-Object {
        (Get-Content $_.FullName -Raw) -notmatch "{%\s*load\s+i18n\s*%}"
    } |
    Select-Object Name, FullName
```

### Contar uso de trans vs texto hardcodeado:
```powershell
# Contar tags {% trans %}
(Get-Content "templates\taller\common\clientes\lista_clientes.html" |
    Select-String "{% trans").Count
```

---

## CONCLUSIONES

1. **Estrategia híbrida funcional:** E_garage usa eficazmente tanto templates específicas como comunes

2. **Buena cobertura Chile:** El mercado principal (Chile español) está bien cubierto

3. **USA inglés bien desarrollado:** 19 archivos específicos para mercado americano

4. **USA español necesita mejora:** Solo 8 archivos, puede limitar adopción hispana

5. **Oportunidad de consolidación:** Algunos módulos (repuestos, reportes) podrían beneficiarse de unificación con i18n

6. **Estructura clara pero mejorable:** La organización actual funciona pero podría ser más intuitiva

---

**Próximos pasos sugeridos:**
1. ✅ Auditar templates de repuestos y reportes para consolidación
2. ✅ Expandir cobertura USA español
3. ✅ Documentar estrategia i18n para el equipo
4. ✅ Implementar tests de cobertura
5. ✅ Considerar reorganización de directorios (opcional)

---

**Fin del análisis i18n**



