# Auditoría de Arquitectura — Verticales eGarage
**Fecha:** 2026-07-28  
**Rama:** prod-good-cache-servicios-20260429  
**Última migración:** 0155_catalogorepuestoempresa_and_more.py  
**Propósito:** Determinar qué existe, qué falta y cuál es el camino seguro para separar tres verticales (Talleres, Desarmadurías, Casas de Repuestos) dentro de la misma aplicación Django.

> **Solo auditoría. Ningún archivo modificado. Ninguna migración creada.**

---

## 1. Resumen Ejecutivo

eGarage es una sola aplicación Django multi-tenant con una sola base de datos. La separación en tres verticales es **técnicamente viable sin dividir repositorios ni despliegues**. El mayor riesgo actual no es de código sino de negocio: **todos los usuarios ven todos los módulos en el menú, y cualquier empresa autenticada puede acceder a las URLs de desarme sin ningún gate por tipo de negocio**.

| Área | Estado |
|---|---|
| Núcleo multi-tenant | Completo y robusto |
| Módulo Talleres | ~80% operativo |
| Módulo Desarmadurías | ~75% operativo |
| Módulo Casa de Repuestos | ~15% — solo inventario básico |
| Diferenciación por vertical | **No existe** |
| Landings especializadas | No existen |
| Onboarding captura tipo de negocio | **No** |
| Protección de URLs por vertical | **No existe** |

---

## 2. Árbol de Archivos Clave

```
gestion_taller/
├── settings/__init__.py          ← settings activo (pytest + runserver)
├── settings/base.py              ← middleware stack real (base.py)
├── settings.py                   ← legacy DigitalOcean (sin EmpresaResolverMiddleware)
├── urls.py                       ← ROOT_URLCONF
└── middleware/
    ├── country_prefix.py
    └── accounts_redirect.py

taller/
├── models/
│   ├── empresa.py                ← Empresa (tenant raíz)
│   ├── configuracion.py          ← ConfiguracionEmpresa (rubro_principal, feature flags)
│   ├── repuesto.py               ← Repuesto + CategoriaRepuesto
│   ├── compra.py                 ← Compra (stub básico)
│   ├── venta.py                  ← Venta (stub básico)
│   ├── vehiculo_desarme.py       ← VehiculoDesarme
│   ├── pieza_desarme.py          ← PiezaDesarme
│   ├── vehiculo_financial.py     ← VehiculoFinancialSnapshot, VehicleFinancialEvent
│   ├── interchange_pieza.py      ← InterchangePieza
│   ├── vendedor_desarme.py       ← VendedorDesarme
│   ├── venta_desarme.py          ← VentaDesarme
│   ├── catalogo_repuesto_empresa.py ← CatalogoRepuestoEmpresa
│   ├── documento.py              ← Documento (cotizaciones, OT)
│   └── ...
├── desarme/                      ← sub-app desarmaduría
│   ├── views.py                  ← 1 500+ líneas
│   ├── views_venta.py
│   ├── views_inventario.py
│   ├── views_pdf.py
│   ├── forms.py
│   ├── services.py
│   ├── catalogo_operativo.py
│   └── catalogo_piezas.py
├── repuestos/                    ← sub-app repuestos
│   ├── views_cbv.py
│   ├── views.py
│   ├── api.py
│   └── urls.py
├── middleware/
│   ├── empresa_resolver.py       ← EmpresaResolverMiddleware (ACTIVO)
│   ├── verificar_suscripcion.py  ← VerificarSuscripcionMiddleware (ACTIVO)
│   ├── onboarding_middleware.py  ← OnboardingMiddleware (DEFINIDO, NO ACTIVO)
│   ├── tenant_isolation.py       ← TenantIsolationMiddleware (DEFINIDO, NO ACTIVO)
│   └── suscripcion.py            ← SuscripcionMiddleware legacy (NO ACTIVO)
├── views/
│   └── onboarding_views.py       ← wizard 3 pasos
├── forms/
│   └── onboarding.py             ← OnboardingIdentidadForm, OnboardingFiscalForm
├── configuracion/
│   ├── rubros_logic.py           ← get_ui_config(), get_roles_permitidos()
│   └── rubros_responsables.py    ← labels por rubro (PARTS → "Vendedor responsable")
├── urls_desarme.py               ← namespace "desarme"
├── urls.py, urls_clientes.py, urls_dashboard.py, ...
└── context_processors/
    ├── empresa_contexto.py       ← expone `empresa` a templates
    ├── feature_flags.py          ← expone country_features (por PAÍS, no por vertical)
    └── ...

templates/
├── base.html                     ← menú principal (2 filas, SIN condicionales por vertical)
├── components/sidebar.html       ← sidebar estático (21 líneas, hardcodeado CL)
├── layouts/app.html              ← incluye sidebar
├── taller/common/
│   └── workspace_home.html       ← workspace SIN diferenciación por vertical
├── taller/desarme/               ← 27 templates operativos
├── onboarding/                   ← paso_identidad.html NO captura vertical
└── public/
    └── landing_chile_completa.html ← 100% orientada a talleres mecánicos
```

---

## 3. Núcleo Compartido — Lo que es 100% común a las tres verticales

| Componente | Archivo | Estado |
|---|---|---|
| `Empresa` | `taller/models/empresa.py:21` | Completo |
| `ConfiguracionEmpresa` | `taller/models/configuracion.py:9` | Completo + rubro |
| `Cliente` | `taller/models/clientes.py` | Completo |
| `Vehiculo` (cliente/taller) | `taller/models/vehiculos.py` | Completo |
| `Documento` (cotización/OT) | `taller/models/documento.py` | Completo |
| `DetalleDocumento` | `taller/models/lineas_documento.py` | Completo |
| Impuestos | `taller/impuestos/engine.py` | Completo |
| Suscripción | `taller/models/suscripcion.py` | Completo |
| `EmpresaResolverMiddleware` | `taller/middleware/empresa_resolver.py` | Activo |
| `VerificarSuscripcionMiddleware` | `taller/middleware/verificar_suscripcion.py` | Activo |
| Auth / allauth | `gestion_taller/settings/base.py` | Activo |
| Country features | `taller/config/country_features.py` | Completo |
| Multi-tenant scoping | `core/models.py:TenantScoped` | Completo |

**Estimación: 70-75% del código es núcleo compartido.**

---

## 4. Modelo Empresa y Relación Usuario-Empresa

**Archivo:** `taller/models/empresa.py:21`

```python
class Empresa(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="empresa"
    )
    pais = models.CharField(choices=PAIS_CHOICES, default="CL")
    plan = models.CharField(choices=PLAN_CHOICES, default="trial")
    onboarding_completado = models.BooleanField(default=False)   # línea 168
    onboarding_step = models.PositiveIntegerField(default=1)     # línea 171
    # ... suscripción, facturación, timezone, etc.
```

**Hallazgos críticos:**
- `Empresa` tiene **relación OneToOne con User** (un dueño por empresa).
- Multi-usuario se maneja via `TeamMember` (resuelto por `EmpresaResolverMiddleware`).
- `Empresa` NO tiene campo `tipo_negocio`, `vertical`, `modulo_desarme` ni ningún equivalente.
- `ConfiguracionEmpresa` (relación OneToOne via `empresa.config`) tiene `rubro_principal` pero este campo solo controla **etiquetas en formularios de documentos**, no acceso a módulos ni menú.

---

## 5. Middleware Multi-Tenant

### Stack activo en producción (`gestion_taller/settings/base.py:55`)

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",          # dinámico
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "taller.middleware.empresa_resolver.EmpresaResolverMiddleware",   # ← inyecta request.empresa
    "taller.middleware.verificar_suscripcion.VerificarSuscripcionMiddleware",  # ← suscripción
]
```

### Middlewares definidos pero NO activos

| Middleware | Archivo | Por qué no está activo |
|---|---|---|
| `OnboardingMiddleware` | `taller/middleware/onboarding_middleware.py` | No está en el stack |
| `TenantIsolationMiddleware` | `taller/middleware/tenant_isolation.py` | No está en el stack |
| `SuscripcionMiddleware` (legacy) | `taller/middleware/suscripcion.py` | Reemplazado por VerificarSuscripcionMiddleware |
| `EmpresaMiddleware` (legacy) | `taller/middleware/empresa_middleware.py` | Reemplazado por EmpresaResolverMiddleware |

### Comportamiento de EmpresaResolverMiddleware

`taller/middleware/empresa_resolver.py:19`

Inyecta `request.empresa`, `request.company`, `request.country` en cada request. Si el usuario está autenticado pero sin empresa, hace logout forzado. Soporta TeamMembers además del owner OneToOne.

**No verifica tipo de negocio. No filtra módulos.**

### Comportamiento de VerificarSuscripcionMiddleware

`taller/middleware/verificar_suscripcion.py:99`

Usa `SubscriptionAccessService.decide()` para permitir, advertir o bloquear por suscripción. Devuelve JSON 403 para requests de API.

**No verifica tipo de negocio. No distingue entre módulo taller, desarme o repuestos.**

---

## 6. Sidebar y Workspace — Estado Actual

### Sidebar principal (`templates/base.html:807-875`)

El menú real está en `templates/base.html`, no en `templates/components/sidebar.html` (ese archivo es un stub de 21 líneas, hardcodeado para `/cl/es/`).

**Fila 1 (todos los usuarios autenticados):**
- ⚙️ Ajustes/Settings
- 👤 Equipo/Team (solo owners: `{% if request.user|is_owner %}`)
- 🚀 Centro/Center
- 👥 Clientes/Clients
- 📄 Documentos/Documents
- ⭐ Extra

**Fila 2 (todos los usuarios autenticados):**
- 🔧 Repuestos/Parts
- 📊 Reportes/Reports
- 🛠️ Servicios/Services
- 🧩 **Desarme/Disassembly** — visible para TODOS sin condición
- 🚗 Vehículos/Vehicles
- 🚪 Salir/Logout

**Hallazgo crítico:** El único condicional en la navegación es `{% if request.user|is_owner %}` para el botón Equipo. **No hay ningún condicional por tipo de negocio, rubro, plan o vertical.**

### Workspace Home (`templates/taller/common/workspace_home.html`)

59 líneas. Muestra tres tarjetas fijas para todos:
1. "Vehicles in workshop" → `{% country_url 'vehiculos:lista_vehiculos' %}`
2. "Open documents" → `/documentos/`
3. **"Disassembly yard"** → `{% country_url 'desarme:lista_vehiculos' %}`

No hay diferenciación por tipo de empresa.

---

## 7. Vertical Talleres — Auditoría

### Funcionalidades existentes

| Funcionalidad | Backend | Templates | URLs | Estado |
|---|---|---|---|---|
| Vehículos (cliente/reparación) | `taller/models/vehiculos.py` | `templates/vehiculos/` | `taller/vehiculos/` | Completo |
| Clientes | `taller/models/clientes.py` | `templates/clientes/` | `taller/clientes/` | Completo |
| Documentos (OT / cotización) | `taller/documentos/` | `templates/documentos/` | `taller/documentos/urls.py` | Completo |
| Técnicos | `taller/models/tecnico.py` | `templates/tecnicos/` | — | Completo |
| Servicios | `taller/servicios/` | `templates/servicios/` | `taller/servicios/urls.py` | Completo |
| Repuestos (consumo en OT) | `taller/models/repuesto.py` | `taller/common/repuestos/` | `taller/repuestos/urls.py` | Completo |
| Inspección de ingreso | `taller/models/inspeccion_ingreso.py` | `templates/inspeccion/` | — | Completo |
| Historial vehículo | `taller/models/historial.py` | — | — | Parcial |
| Kilometraje | `taller/models/kilometraje.py` | — | — | Parcial |
| Reportes | `taller/reportes/views.py` | `templates/business_intelligence/` | — | Completo |
| Agenda / Citas | `taller/models/cita.py` | — | — | Parcial |

### Rubro en ConfiguracionEmpresa

`taller/models/configuracion.py:143`

`RUBRO_CHOICES` incluye: WORKSHOP, WORKSHOP_MOTO, WORKSHOP_HEAVY, EXHAUST, PARTS, TIRE, BODYSHOP, DETAILING, ELECTRIC, GLASS_AUDIO, FLEET, MIXED.

`get_secciones_visibles()` (línea 214) ajusta qué secciones aparecen en el formulario de documentos según `rubro_principal`. Este es el **único lugar donde el rubro tiene efecto real actualmente**.

---

## 8. Vertical Desarmadurías — Auditoría

### Modelos

| Modelo | Archivo | Estado |
|---|---|---|
| `VehiculoDesarme` | `taller/models/vehiculo_desarme.py` | Completo |
| `PiezaDesarme` | `taller/models/pieza_desarme.py` | Completo |
| `VentaDesarme` | `taller/models/venta_desarme.py` | Completo |
| `VendedorDesarme` | `taller/models/vendedor_desarme.py` | Completo |
| `InterchangePieza` | `taller/models/interchange_pieza.py` | Completo |
| `VehiculoFinancialSnapshot` | `taller/models/vehiculo_financial.py:10` | Completo |
| `VehicleFinancialEvent` | `taller/models/vehiculo_financial.py:64` | Completo |
| `CatalogoRepuestoEmpresa` | `taller/models/catalogo_repuesto_empresa.py` | Completo |

### Vistas

| Vista/Módulo | Archivo | Estado |
|---|---|---|
| CRUD vehículos de desarme | `taller/desarme/views.py:562-801` | Completo |
| Inventario por vehículo | `taller/desarme/views_inventario.py` | Completo |
| Venta rápida (mini-POS) | `taller/desarme/views_venta.py` | Completo |
| PDF de venta | `taller/desarme/views_pdf.py` | Completo |
| Dashboard financiero | `taller/desarme/views.py` | Completo |
| Reportes | `templates/taller/desarme/reportes.html` | Parcial |
| Interchange | `taller/desarme/views.py` | Completo |
| Scanner vehículo | `templates/taller/desarme/scanner_vehiculo.html` | Completo |
| Kiosco / tienda pública | `templates/public/storefront/kiosko.html` | Completo |

### Templates (27 en `templates/taller/desarme/`)

```
configurar_catalogo.html
confirmar_venta_desde_inventario.html
crear_interchange.html
dashboard.html
dashboard_financiero.html
inventario_inteligente.html
inventario_vehiculo.html
lista_interchange.html
lista_piezas.html
lista_vehiculos.html
lista_vehiculos_partial.html
pieza_form.html
pieza_suelta_form.html
reportes.html
revisar_vehiculo.html
scanner_vehiculo.html
unavailable.html
vehiculo_form.html
ver_vehiculo.html
partials/_inventario_drawer.html
... (7 más)
```

### URLs (`taller/urls_desarme.py`)

Namespace `desarme`. Rutas bajo `/cl/es/desarme/` y `/us/en/desarme/`.

### Seguridad actual del módulo Desarme

- Todas las vistas tienen `@login_required` (líneas 57, 80, 258, 374, 561, 607, 706, 755, 802, 864, 925, 992, 1028, 1099, 1207...)
- Todas verifican `empresa = _empresa_or_redirect(request)` o equivalente
- **No existe ningún gate por tipo de negocio ni por plan que incluya/excluya el módulo de desarme**
- Un taller mecánico recién registrado puede acceder a `/cl/es/desarme/vehiculos/` sin restricción

### PiezaDesarme y Repuesto — relación

`taller/models/pieza_desarme.py:72`

```python
repuesto = models.ForeignKey("taller.Repuesto", on_delete=models.SET_NULL, null=True, blank=True)
part = models.ForeignKey("taller.Part", on_delete=models.SET_NULL, null=True, blank=True)
```

Una pieza de desarme puede opcionalmente vincularse a un Repuesto del catálogo. Esta es la única dependencia entre los dos módulos.

---

## 9. Vertical Casa de Repuestos — Auditoría

### Qué existe

| Componente | Archivo | Estado |
|---|---|---|
| Modelo `Repuesto` | `taller/models/repuesto.py:41` | Básico |
| Modelo `CategoriaRepuesto` | `taller/models/repuesto.py:11` | Básico |
| `Compra` | `taller/models/compra.py` | **Stub** (4 campos) |
| `Venta` | `taller/models/venta.py` | **Stub** (5 campos) |
| `RepuestoListView` | `taller/repuestos/views_cbv.py:95` | Funcional |
| `RepuestoCreateView` | `taller/repuestos/views_cbv.py:194` | Funcional |
| `RepuestoUpdateView` | `taller/repuestos/views_cbv.py:254` | Funcional |
| Rubro `PARTS` en ConfiguracionEmpresa | `taller/models/configuracion.py:159` | Existe |
| `get_secciones_visibles()` para PARTS | `taller/models/configuracion.py:235` | Funcional |

### Qué falta para vender a una Casa de Repuestos profesional

| Funcionalidad | Estado |
|---|---|
| Bodegas / almacenes | No existe |
| Movimientos de inventario (entradas/salidas) | No existe |
| Recepción de mercadería | No existe |
| Orden de compra a proveedor | No existe |
| Ficha de proveedor | No existe (campo texto en Repuesto) |
| Búsqueda avanzada de catálogo | No existe |
| Trazabilidad de stock | No existe |
| Dashboard de rentabilidad por producto | No existe |
| Gestión de devoluciones | No existe |
| Códigos de barras / QR | No existe |
| Integración con catálogos externos (TecDoc, etc.) | No existe |
| Venta directa sin documento OT | Solo via documento |
| Alertas de stock mínimo (UI) | Existe en lista (campo stock_minimo) |

### Evaluación comercial

El módulo `Repuesto` actual fue construido para **gestionar consumo de repuestos en órdenes de trabajo de taller**, no para administrar el inventario de una casa de repuestos. La diferencia es sustancial:

- **Taller usa Repuesto:** selecciona una pieza al crear un documento, descuenta stock automáticamente.
- **Casa de Repuestos necesita:** compras a proveedor, recepción, stock por bodega, ventas directas, devoluciones, márgenes, rentabilidad por SKU.

**Conclusión: Casa de Repuestos como vertical comercial independiente requiere construcción nueva, no adaptación menor.**

---

## 10. Portal Público y Landings

### Estado actual

| Template / URL | Contenido | Estado |
|---|---|---|
| `templates/public/landing_chile_completa.html` | 100% talleres mecánicos. Frases como "creado por mecánicos para dueños de talleres" | Existe, orientado solo a talleres |
| `templates/landing_inicio.html` | Sin auditoría de contenido | Existe |
| `/cl/es/` | Landing principal Chile | Existe |
| `/us/en/` | Landing principal USA | Existe |
| `/desarmadurias/` | **No existe** | — |
| `/talleres/` | **No existe** | — |
| `/repuestos/` | **No existe** | — |

### Estructura de URLs por país

`gestion_taller/urls.py` registra namespaces por país:
- `/cl/es/` → Chile Español
- `/us/en/` → USA English
- `/us/es/` → USA Español
- `/mx/es/` → México

Las rutas `/cl/es/desarme/`, `/us/en/desarme/` existen y funcionan. No hay rutas `/desarmadurias/` como landing pública.

---

## 11. Campo de Tipo de Negocio — ¿Existe algo?

### Inventario completo de campos relacionados a vertical/tipo de negocio

| Campo | Modelo | Archivo | Efecto actual |
|---|---|---|---|
| `pais` | `Empresa` | `empresa.py:100` | Define moneda, timezone, URLs, impuestos |
| `plan` | `Empresa` | `empresa.py:141` | Define cupo de usuarios y suscripción |
| `rubro_principal` | `ConfiguracionEmpresa` | `configuracion.py:166` | Controla etiquetas en documentos y secciones visibles del formulario de OT |
| `rubros` | `ConfiguracionEmpresa` | `configuracion.py:178` | JSONField, sin efecto visible en código actual |
| `usa_vehiculos` | `ConfiguracionEmpresa` | `configuracion.py` | Feature flag de sección en formulario |
| `usa_servicios` | `ConfiguracionEmpresa` | `configuracion.py` | Feature flag de sección en formulario |
| `usa_otros_servicios` | `ConfiguracionEmpresa` | `configuracion.py` | Feature flag de sección en formulario |
| `usa_kilometraje` | `ConfiguracionEmpresa` | `configuracion.py` | Feature flag de sección en formulario |

### Conclusión

Ya existe una **base parcial** de diferenciación por rubro en `ConfiguracionEmpresa.rubro_principal`, pero su efecto actual es **solo cosmético** (etiquetas) y **solo dentro del formulario de documentos**. No controla:
- Qué menú se muestra
- A qué URLs puede acceder la empresa
- Qué dashboard se carga
- Qué onboarding recibe

El campo `rubros` (JSONField) existe pero no tiene lógica asociada en el código.

---

## 12. Onboarding y Registro

### Flujo actual

```
/accounts/signup/ → crea User + Empresa
    ↓
/cl/es/onboarding/identidad/  (paso 1)
    campos: nombre_taller, logo, lema
    ↓
/cl/es/onboarding/finalizar/  (paso 3, el paso 2 se salta automáticamente)
    checkbox: cargar_demo
    ↓
empresa.onboarding_completado = True
    ↓
redirect → taller:dashboard
```

### Archivos involucrados

- `taller/views/onboarding_views.py` — vistas del wizard
- `taller/forms/onboarding.py` — formularios (identidad + fiscal + contacto)
- `templates/onboarding/paso_identidad.html` — solo pide nombre_taller, logo, lema
- `taller/middleware/onboarding_middleware.py` — **no está activo en el stack**

### Hallazgos

1. El onboarding **no captura el tipo de negocio** en ningún paso.
2. El formulario `OnboardingIdentidadForm` (`forms/onboarding.py`) solo tiene `nombre_taller` y `logo`.
3. El campo `rubro_principal` en `ConfiguracionEmpresa` se establece por defecto en `"WORKSHOP"` vía `CompanyDefaultsService`, nunca por elección del usuario.
4. El `OnboardingMiddleware` está definido pero no está en el stack activo. No redirige a onboarding.
5. El paso 2 (fiscal) se salta automáticamente y se aplica por país vía `CompanyDefaultsService`.

---

## 13. Seguridad y Permisos — Análisis de Acceso por URL

### Protección real en vistas de desarmaduría

```python
# taller/desarme/views.py:57-67
@login_required
def api_vendedores_buscar(request):
    empresa = _empresa_or_redirect(request)  # verifica empresa != None
    ...

# taller/desarme/views.py:374
@login_required
def lista_vehiculos(request):
    empresa = _empresa_or_redirect(request)
    VehiculoDesarme.objects.filter(empresa=empresa)  ← aislamiento por empresa
```

### Lo que SÍ está protegido

- Aislamiento por empresa en todas las queries (TenantScoped, filtro por `empresa`)
- Login requerido (`@login_required` en todas las vistas de desarme)
- Suscripción activa (`VerificarSuscripcionMiddleware`)

### Lo que NO está protegido

- **No existe ningún gate que verifique si la empresa tiene el módulo de desarme habilitado**
- Un taller recién creado puede acceder a `/cl/es/desarme/vehiculos/` y operar normalmente
- Un usuario de PARTS puede acceder al módulo de desarme sin restricción
- La visibilidad del menú es idéntica para todos los tipos de empresa

### Evaluación de riesgo

**Riesgo actual: BAJO** para datos (aislamiento multi-tenant robusto).  
**Riesgo comercial: ALTO** — no es posible vender "desarmaduría premium" sin un módulo de autorización que lo soporte.

---

## 14. Configuración de Módulos — Opción Recomendada

### Análisis de opciones

**Opción A — Campo único `tipo_negocio` en Empresa:**
```python
tipo_negocio = CharField(choices=[("TALLER", ...), ("DESARMADURIA", ...), ("REPUESTOS", ...)])
```
❌ Descartada: no soporta empresas multiverticales (Atlanta Reciclajes necesita ser taller + desarmaduría).

**Opción B — Flags booleanos en ConfiguracionEmpresa:**
```python
modulo_taller = BooleanField(default=True)
modulo_desarmaduria = BooleanField(default=False)
modulo_repuestos = BooleanField(default=False)
```
✅ Simple, backward-compatible, soporta multivetical.  
⚠️ Extiende una tabla ya grande, mezcla configuración y módulos.

**Opción C — Tabla normalizada `EmpresaModulo`:**
```python
class EmpresaModulo(models.Model):
    empresa = ForeignKey("taller.Empresa", related_name="modulos")
    codigo = CharField(choices=[("TALLER", ...), ("DESARMADURIA", ...), ("REPUESTOS", ...)])
    activo = BooleanField(default=True)
    class Meta:
        constraints = [UniqueConstraint(fields=["empresa", "codigo"], ...)]
```
✅ Extensible, soporta multivertical, permite configuración futura por módulo.  
⚠️ Requiere migración nueva + backfill.

**Opción D — Usar `rubro_principal` existente:**
❌ Ya existe pero solo controla formulario de documentos, no módulos. Extenderlo rompería su semántica actual.

### Recomendación

**Opción C (`EmpresaModulo`)** para el mediano plazo.  
**Opción B (flags en ConfiguracionEmpresa)** como paso intermedio de bajo riesgo.

La secuencia recomendada:
1. Agregar `modulo_desarmaduria = BooleanField(default=True)` en `ConfiguracionEmpresa` (retrocompatible: todas las empresas existentes mantienen acceso).
2. Conectar el flag al menú y al middleware.
3. En el futuro, migrar a tabla `EmpresaModulo` cuando se tenga más claridad sobre qué otros módulos se van a controlar.

---

## 15. Impacto en Base de Datos

### Migración mínima viable (solo para habilitar menú diferenciado)

```python
# En ConfiguracionEmpresa:
modulo_taller = models.BooleanField(default=True)
modulo_desarmaduria = models.BooleanField(default=True)   # True para no romper existentes
modulo_repuestos = models.BooleanField(default=True)
```

- **Backfill necesario:** Ninguno. `default=True` cubre todas las empresas existentes.
- **Riesgo de downtime:** Ninguno (solo ADD COLUMN con default).
- **Impacto multi-tenant:** Ninguno (el campo es por empresa).
- **Impacto en producción:** Ninguno (modo `default=True` no cambia comportamiento actual).

### Migración completa (tabla EmpresaModulo)

Requeriría:
1. Crear tabla `EmpresaModulo`.
2. Backfill: crear registro `TALLER + activo=True` para todas las empresas existentes.
3. Crear registro `DESARMADURIA + activo=True` para empresas que tengan al menos un `VehiculoDesarme`.
4. Mantener retro-compatibilidad hasta remover flags booleanos.

---

## 16. Plan de Implementación por Etapas

### Etapa 0 — Esta semana, sin migración (solo templates)
**Objetivo:** Landings diferenciadas en el portal público.

- Crear `templates/public/landing_talleres.html`
- Crear `templates/public/landing_desarmadurias.html`
- Crear `templates/public/landing_repuestos.html`
- Crear vistas en `taller/views/landing_views.py` (3 vistas simples)
- Agregar URLs a `taller/urls_public.py` o `gestion_taller/urls.py`
- **No modificar base.html ni sidebar. No crear migraciones.**
- **Riesgo:** Ninguno. Rollback: eliminar los 4 archivos nuevos.

### Etapa 1 — Migración mínima (1 semana)
**Objetivo:** Campo de módulo en ConfiguracionEmpresa + onboarding captura vertical.

- Agregar `modulo_desarmaduria`, `modulo_repuestos`, `modulo_taller` a `ConfiguracionEmpresa`.
- Migración: `default=True` en todos — sin backfill, sin downtime.
- Modificar `onboarding/paso_identidad.html` para agregar selector de tipo de negocio.
- `OnboardingIdentidadForm` captura y guarda la selección.
- `CompanyDefaultsService` aplica defaults según tipo seleccionado.
- **Riesgo:** Bajo. Rollback: revertir migración + templates.

### Etapa 2 — Menú diferenciado (1 semana)
**Objetivo:** El menú muestra solo los módulos de la vertical de la empresa.

- Modificar `empresa_contexto` context processor para incluir `modulos_activos`.
- Modificar `templates/base.html` líneas 807-875 con condicionales `{% if modulo_desarmaduria %}`.
- **No crear nuevo middleware.** Solo condicionales en template.
- **Riesgo:** Medio. Rollback: revertir cambio en base.html.

### Etapa 3 — Autorización backend (2 semanas)
**Objetivo:** Un taller que navega a `/cl/es/desarme/vehiculos/` recibe 403.

- Crear decorator `@requiere_modulo("DESARMADURIA")` en `taller/decorators.py`.
- Aplicar a vistas en `taller/desarme/views.py`, `views_venta.py`, `views_inventario.py`.
- **No modificar el middleware stack** para esta etapa.
- **Riesgo:** Medio. Requiere pruebas de regresión en todas las vistas de desarme.

### Etapa 4 — Onboarding especializado (1 semana)
**Objetivo:** Un usuario que elige "Desarmaduría" ve un wizard diferente.

- Crear `templates/onboarding/paso_identidad_desarmaduria.html`.
- El paso de identidad elige template según la vertical seleccionada.
- **Riesgo:** Bajo. Rollback: revertir cambio en vista de onboarding.

### Etapa 5 — Casa de Repuestos (1-3 meses)
**Objetivo:** Funcionalidades mínimas para una casa de repuestos profesional.

- Modelo `Proveedor` (ficha completa).
- Modelo `OrdenCompra` con líneas.
- Modelo `RecepcionMercaderia`.
- Modelo `MovimientoStock`.
- Vistas y templates para cada modelo.
- Dashboard de rentabilidad por SKU.
- **Riesgo:** Alto. Es construcción nueva. Requiere diseño cuidadoso para no romper el módulo `Repuesto` existente que usan los talleres.

---

## 17. Matriz Funcional Final

| Área | Compartida | Taller | Desarmaduría | Casa Repuestos | Estado | Acción |
|---|---|---|---|---|---|---|
| Empresa | Sí | Sí | Sí | Sí | Completo | Agregar campo modulo |
| ConfiguracionEmpresa | Sí | Sí | Sí | Sí | Completo | Agregar flags de módulo |
| Clientes | Sí | Sí | Sí | Sí | Completo | Mantener |
| Vehículos (cliente) | Sí | Sí | Parcial | No | Completo | Mantener |
| VehiculoDesarme | No | No | Sí | No | Completo | Especializar, agregar gate |
| PiezaDesarme | No | No | Sí | Parcial | Completo | Especializar |
| Documentos (OT/cotización) | Sí | Sí | Sí | Sí | Completo | Mantener |
| Repuesto (catálogo) | Sí | Sí | Vinculado | Sí | Completo | Mantener, extender para repuestos |
| Compra | No | No | No | Sí | **Stub** | Construir |
| Venta directa | No | No | Sí (VentaDesarme) | No | Parcial para desarme | Extender para repuestos |
| Inventario con movimientos | No | No | No | Sí | **No existe** | Construir |
| Interchange | No | No | Sí | Posible | Completo | Especializar |
| Dashboard financiero | No | No | Sí | No | Completo para desarme | Construir para repuestos |
| Kiosco público | No | No | Sí | Posible | Completo | Mantener |
| Proveedores (ficha) | No | No | Sí (VendedorDesarme) | Sí | Parcial | Generalizar |
| Técnicos/Mecánicos | No | Sí | No | No | Completo | Mantener en vertical taller |
| Servicios | No | Sí | No | No | Completo | Mantener en vertical taller |
| Reportes | Parcial | Sí | Sí (financiero) | No | Parcial | Extender |
| Menú diferenciado | **No existe** | — | — | — | No existe | **Primera prioridad** |
| Gate de autorización URL | **No existe** | — | — | — | No existe | Segunda prioridad |
| Landing especializada | **No existe** | — | — | — | No existe | **Etapa 0** |
| Onboarding captura vertical | **No existe** | — | — | — | No existe | Etapa 1 |

---

## 18. Deuda Técnica Relevante

| Problema | Archivo | Severidad |
|---|---|---|
| Sidebar en `components/sidebar.html` hardcodeado para CL, no es el sidebar real | `templates/components/sidebar.html` | MEDIO |
| El sidebar real está en `base.html:807` sin condicionales por vertical | `templates/base.html:807` | ALTO |
| `OnboardingMiddleware` definido pero no activo | `taller/middleware/onboarding_middleware.py` | MEDIO |
| `TenantIsolationMiddleware` y `SuscripcionMiddleware` duplican lógica que ya está en el stack activo | `taller/middleware/` | BAJO |
| `rubro_principal` tiene código `PARTS` pero no controla el módulo de repuestos | `taller/models/configuracion.py:166` | MEDIO |
| `Compra` y `Venta` son stubs de 15-19 líneas, sin líneas de detalle ni trazabilidad | `taller/models/compra.py`, `venta.py` | ALTO (para casa de repuestos) |
| `EmpresaMiddleware` legacy duplica `EmpresaResolverMiddleware` | `taller/middleware/empresa_middleware.py` | BAJO |
| `gestion_taller/settings.py` (raíz) no tiene `EmpresaResolverMiddleware` | `gestion_taller/settings.py:20` | MEDIO |
| Workspace hardcodeado muestra desarme a todos sin condición | `templates/taller/common/workspace_home.html:49` | ALTO |

---

## 19. Respuestas a Preguntas Clave

**¿Puede eGarage soportar 3 verticales sin dividirse?**  
Sí. La arquitectura multi-tenant es robusta. Solo se necesita un campo de módulo y condicionales en el menú.

**¿Qué % es realmente compartido?**  
~70-75%: Empresa, ConfiguracionEmpresa, Clientes, Vehículos, Documentos, Impuestos, Suscripción, Auth, middleware.

**¿Qué módulos son exclusivos de talleres?**  
Técnicos/Mecánicos, Servicios, Citas, Inspección de ingreso.

**¿Qué módulos son exclusivos de desarmadurías?**  
VehiculoDesarme, PiezaDesarme, VentaDesarme, VendedorDesarme, InterchangePieza, VehiculoFinancialSnapshot, VehicleFinancialEvent, CatalogoRepuestoEmpresa, kiosco.

**¿Qué módulos reales existen para casas de repuestos?**  
Repuesto + CategoriaRepuesto (completo). Compra/Venta (stubs). Proveedor (campo texto en Repuesto). Todo lo demás: **no existe**.

**¿Cuál es la fuente de verdad para módulos habilitados?**  
Hoy: no existe. La propuesta es `ConfiguracionEmpresa` con flags booleanos como paso 1.

**¿Cómo proteger el acceso por URL?**  
Decorator `@requiere_modulo("DESARMADURIA")` aplicado en las vistas. El middleware actual no distingue módulos.

**¿Cómo construir los menús?**  
Condicionales en `templates/base.html:807` usando `empresa.config.modulo_desarmaduria`. El context processor `empresa_contexto` ya expone `empresa`.

**¿Cómo capturar la vertical en onboarding?**  
Agregar un selector en `paso_identidad.html` y guardarlo en `ConfiguracionEmpresa.rubro_principal` o en los nuevos flags booleanos.

**¿Qué migraciones serían necesarias?**  
Solo una migración para agregar los campos booleanos con `default=True`. Sin downtime, sin backfill manual.

**¿Qué cambios pueden romper producción?**  
- Modificar `templates/base.html` sin pruebas en todos los países.
- Agregar middleware al stack sin probar el flujo de onboarding.
- Establecer `default=False` en los flags de módulo sin backfill previo.

**¿Qué falta para posicionarse como software para desarmadurías?**  
El módulo está ~75% completo. Falta: gate de autorización por módulo, landing propia, onboarding especializado, y pulir algunos reportes.

**¿Qué falta para vender a casas de repuestos?**  
Casi todo: proveedores, órdenes de compra, recepción, movimientos de stock, bodegas, trazabilidad, devoluciones. Es construcción de 1-3 meses.

---

## 20. Decisiones que Requieren Aprobación

1. **¿Flags booleanos en ConfiguracionEmpresa o tabla EmpresaModulo?** — Recomendación: flags primero, tabla después.
2. **¿`default=True` en todos los módulos para empresas existentes?** — Recomendación: sí, para no interrumpir operaciones actuales.
3. **¿El rubro "DESARMADURIA" se maneja separado del rubro "WORKSHOP"?** — Sí, son verticales distintas en el modelo de negocio.
4. **¿Cuándo construir la vertical Casa de Repuestos?** — Depende de demanda real. No bloquea las otras dos verticales.
5. **¿El kiosco público sigue siendo exclusivo de desarmadurías o también lo usarán casas de repuestos?** — Decisión pendiente de producto.

---

## 21. Archivos a Crear en Implementación Futura

```
templates/public/landing_talleres.html              (Etapa 0)
templates/public/landing_desarmadurias.html         (Etapa 0)
templates/public/landing_repuestos.html             (Etapa 0)
taller/views/landing_views.py                       (Etapa 0)
taller/migrations/XXXX_add_modulos_empresa.py       (Etapa 1)
templates/onboarding/paso_identidad_desarmaduria.html  (Etapa 4)
taller/decorators.py (función requiere_modulo)      (Etapa 3)
taller/models/proveedor.py                          (Etapa 5)
taller/models/orden_compra.py                       (Etapa 5)
taller/models/movimiento_stock.py                   (Etapa 5)
```

## 22. Archivos a Modificar en Implementación Futura

```
taller/models/configuracion.py          (Etapa 1: agregar flags)
taller/forms/onboarding.py             (Etapa 1: agregar selector vertical)
templates/onboarding/paso_identidad.html (Etapa 1: agregar selector)
templates/base.html                    (Etapa 2: condicionales en menú)
templates/taller/common/workspace_home.html (Etapa 2: workspace diferenciado)
taller/deserme/views.py                (Etapa 3: agregar @requiere_modulo)
taller/desarme/views_venta.py          (Etapa 3)
taller/desarme/views_inventario.py     (Etapa 3)
taller/context_processors/empresa_contexto.py (Etapa 2: exponer modulos_activos)
```

---

*Auditoría generada el 2026-07-28. Ningún archivo fue modificado durante la auditoría.*
