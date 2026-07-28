# eGarage — Arquitectura de Verticales V1
**Versión:** 1.0  
**Fecha:** 2026-07-28  
**Estado:** Diseño aprobado — pendiente de implementación  
**Rama:** feature/vertical-architecture-v1  
**Auditoría base:** docs/auditorias/auditoria_final_verticales_egarage.md

---

## Principios de Diseño

1. **Una sola aplicación.** Un repositorio, un servidor, una base de datos, una autenticación.
2. **Cambios incrementales.** Cada etapa es independiente, reversible y verificable antes de la siguiente.
3. **Retrocompatibilidad total.** Las empresas existentes no deben notar ningún cambio hasta que el administrador active su vertical.
4. **Autorización en backend, no solo en frontend.** Ocultar un enlace del menú no basta; las URLs deben protegerse.
5. **El `rubro_principal` existente es el punto de anclaje.** Ya existe en `ConfiguracionEmpresa`. No se duplicará con otro campo; se extenderá con flags de módulo.

---

## Modelo Mental

```
eGarage SaaS
│
├── Portal Público
│   ├── / (selector o landing general)
│   ├── /talleres/          → landing vertical Talleres
│   ├── /desarmadurias/     → landing vertical Desarmadurías
│   └── /repuestos/         → landing vertical Casas de Repuestos
│
├── Core (compartido por todas las verticales)
│   ├── Empresa (tenant raíz)
│   ├── ConfiguracionEmpresa (rubro, módulos, flags)
│   ├── Usuario / TeamMember
│   ├── Cliente
│   ├── Vehículo (cliente/reparación)
│   ├── Documento (cotización / OT)
│   ├── Impuestos
│   ├── Suscripción / Plan
│   ├── Auditoría
│   └── Notificaciones
│
├── Vertical Talleres
│   ├── Técnicos / Mecánicos
│   ├── Servicios
│   ├── Órdenes de Trabajo
│   ├── Cotizaciones
│   ├── Citas / Agenda
│   ├── Inspección de ingreso
│   ├── Historial del vehículo
│   └── Repuestos (consumo en OT)
│
├── Vertical Desarmadurías
│   ├── VehiculoDesarme
│   ├── PiezaDesarme
│   ├── VentaDesarme
│   ├── VendedorDesarme
│   ├── Interchange
│   ├── Kiosco público
│   ├── Ciclo de vida del vehículo
│   └── Finanzas por vehículo (snapshot, eventos)
│
└── Vertical Casas de Repuestos
    ├── Proveedor (ficha completa)
    ├── OrdenCompra
    ├── RecepcionMercaderia
    ├── MovimientoStock
    ├── CatalogoProducto
    ├── Bodega
    ├── VentaRepuesto (directa, sin OT)
    └── RentabilidadSKU
```

---

## 1. Núcleo Compartido (Core)

### 1.1 Modelo Empresa

**Archivo actual:** `taller/models/empresa.py:21`

El modelo `Empresa` permanece sin cambios estructurales. Su función es ser el tenant raíz. No llevará `tipo_negocio` ni `vertical` directamente.

```python
# Sin cambios en Empresa para la arquitectura de verticales.
# Los módulos habilitados vivirán en ConfiguracionEmpresa.
```

### 1.2 ConfiguracionEmpresa — Extensión de Módulos

**Archivo actual:** `taller/models/configuracion.py:9`

Este es el único modelo que se extiende en la Etapa 1. Se agregarán tres flags booleanos.

```python
class ConfiguracionEmpresa(models.Model):
    # ... campos actuales sin modificar ...

    # ── MÓDULOS HABILITADOS (nuevo, Etapa 1) ──────────────────────────────────
    modulo_taller = models.BooleanField(
        default=True,
        verbose_name="Módulo Talleres habilitado",
        help_text="Activa órdenes de trabajo, técnicos, servicios y agenda.",
    )
    modulo_desarmaduria = models.BooleanField(
        default=True,
        verbose_name="Módulo Desarmadurías habilitado",
        help_text="Activa vehículos de desarme, inventario de piezas, interchange y kiosco.",
    )
    modulo_repuestos = models.BooleanField(
        default=True,
        verbose_name="Módulo Casa de Repuestos habilitado",
        help_text="Activa catálogo, proveedores, compras y ventas directas de repuestos.",
    )
```

**Decisión de diseño — `default=True` en los tres:**
- Todas las empresas existentes mantienen acceso completo sin intervención manual.
- El onboarding nuevo seteará `modulo_taller=True` y `modulo_desarmaduria=False` por defecto para talleres nuevos.
- El administrador puede activar/desactivar módulos desde el panel admin de Django.

**Relación con `rubro_principal`:**
- `rubro_principal` controla **presentación** (etiquetas, secciones del formulario de documentos).
- Los nuevos flags controlan **acceso** (menú, URLs, dashboard).
- No son redundantes: una empresa puede ser `WORKSHOP` pero tener `modulo_desarmaduria=True`.

### 1.3 Tabla EmpresaModulo (Etapa 5+ — opcional)

Si en el futuro se necesita granularidad por submódulo (ej. habilitar interchange pero no kiosco), se migra a:

```python
class EmpresaModulo(models.Model):
    empresa = models.ForeignKey("taller.Empresa", on_delete=models.CASCADE, related_name="modulos")
    codigo = models.CharField(
        max_length=30,
        choices=[
            ("TALLER", "Taller y servicios"),
            ("DESARMADURIA", "Desarmaduría"),
            ("REPUESTOS", "Casa de repuestos"),
            ("KIOSCO", "Kiosco público"),
            ("INTERCHANGE", "Interchange"),
        ],
    )
    activo = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["empresa", "codigo"], name="uq_empresa_modulo")
        ]
```

Esta tabla no se implementa en las primeras etapas. Los tres flags booleanos son suficientes para los próximos 6-12 meses.

---

## 2. Sistema de Autorización por Módulo

### 2.1 Decorator `@requiere_modulo`

**Archivo futuro:** `taller/decorators.py`

```python
from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import redirect

_MODULO_FIELD = {
    "TALLER": "modulo_taller",
    "DESARMADURIA": "modulo_desarmaduria",
    "REPUESTOS": "modulo_repuestos",
}

def requiere_modulo(codigo: str):
    """
    Decorador que verifica si la empresa tiene habilitado un módulo.
    Uso: @requiere_modulo("DESARMADURIA")
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            empresa = getattr(request, "empresa", None)
            if empresa is None:
                return redirect("account_login")

            config = getattr(empresa, "config", None)
            field = _MODULO_FIELD.get(codigo)
            if field and config and not getattr(config, field, True):
                # Módulo no habilitado: devolver 403 o redirigir a upgrade
                if request.headers.get("x-requested-with") == "XMLHttpRequest":
                    from django.http import JsonResponse
                    return JsonResponse({"error": "Módulo no habilitado"}, status=403)
                return HttpResponseForbidden("Módulo no habilitado para tu empresa.")

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
```

### 2.2 Mixin para Class-Based Views

**Archivo futuro:** `taller/mixins.py` (extensión del existente)

```python
class RequiereModuloMixin:
    modulo_requerido: str = None  # "TALLER" | "DESARMADURIA" | "REPUESTOS"

    def dispatch(self, request, *args, **kwargs):
        if self.modulo_requerido:
            empresa = getattr(request, "empresa", None)
            config = getattr(empresa, "config", None) if empresa else None
            field = _MODULO_FIELD.get(self.modulo_requerido)
            if field and config and not getattr(config, field, True):
                return HttpResponseForbidden("Módulo no habilitado.")
        return super().dispatch(request, *args, **kwargs)
```

### 2.3 Aplicación por módulo

| Módulo | Archivos a decorar |
|---|---|
| DESARMADURIA | `taller/desarme/views.py`, `views_venta.py`, `views_inventario.py`, `views_pdf.py` |
| REPUESTOS (vertical) | Vistas nuevas de la Etapa 5 |
| TALLER | Sin decorador en Etapa inicial (es el módulo por defecto) |

**El decorador no se aplica a:**
- Vistas del núcleo compartido (documentos, clientes, vehículos de reparación).
- Vistas de kiosco público (son rutas `/public/`, no requieren empresa autenticada).
- Vistas de administración (`/admin/`).

---

## 3. Navegación

### 3.1 Menú Principal — Diseño Objetivo

**Archivo a modificar:** `templates/base.html:807-875`

El menú se divide en **fila de núcleo** (siempre visible) y **bloques de vertical** (condicionales).

```html
{# Fila núcleo: siempre visible para todos #}
<div class="nav-row-core">
  ⚙️ Ajustes
  {% if request.user|is_owner %}👤 Equipo{% endif %}
  🚀 Centro
  👥 Clientes
  📄 Documentos
  📊 Reportes
  🚪 Salir
</div>

{# Bloque Taller: visible si modulo_taller #}
{% if empresa.config.modulo_taller %}
<div class="nav-row-taller">
  🚗 Vehículos
  🛠️ Servicios
  🔧 Repuestos (consumo)
  ⭐ Extra
</div>
{% endif %}

{# Bloque Desarmaduría: visible si modulo_desarmaduria #}
{% if empresa.config.modulo_desarmaduria %}
<div class="nav-row-desarme">
  🧩 Desarme
  🔍 Interchange
  🏪 Kiosco
</div>
{% endif %}

{# Bloque Repuestos: visible si modulo_repuestos #}
{% if empresa.config.modulo_repuestos %}
<div class="nav-row-repuestos">
  📦 Catálogo
  🚚 Proveedores
  📥 Compras
</div>
{% endif %}
```

### 3.2 Context Processor — `modulos_activos`

**Archivo a modificar:** `taller/context_processors/empresa_contexto.py`

```python
def empresa_contexto(request):
    if not request.user.is_authenticated:
        return {"empresa": None, "modulos_activos": {}}
    try:
        empresa = request.user.empresa
        config = getattr(empresa, "config", None)
        modulos_activos = {
            "taller": getattr(config, "modulo_taller", True) if config else True,
            "desarmaduria": getattr(config, "modulo_desarmaduria", True) if config else True,
            "repuestos": getattr(config, "modulo_repuestos", True) if config else True,
        }
        return {
            "empresa": empresa,
            "nombre_taller": getattr(empresa, "nombre_taller", "eGarage"),
            "modulos_activos": modulos_activos,
        }
    except Exception:
        return {"empresa": None, "nombre_taller": None, "modulos_activos": {}}
```

En los templates: `{% if modulos_activos.desarmaduria %}` en lugar de `{% if empresa.config.modulo_desarmaduria %}`. Más limpio y sin acoplamiento al modelo.

### 3.3 Sidebar Lateral

El archivo `templates/components/sidebar.html` (actualmente un stub de 21 líneas hardcodeado para CL) se reescribirá en la Etapa 2 para usar las mismas variables condicionales. Hasta entonces permanece sin cambios.

---

## 4. Dashboards por Vertical

### 4.1 Arquitectura de Dashboards

No se crean tres dashboards distintos. Existe un **dashboard base** con **secciones condicionales** por módulo.

```
templates/dashboard/
├── index.html                    ← base, incluye secciones
├── sections/
│   ├── _core_metrics.html        ← siempre visible (clientes, documentos, suscripción)
│   ├── _taller_metrics.html      ← si modulo_taller
│   ├── _desarme_metrics.html     ← si modulo_desarmaduria
│   └── _repuestos_metrics.html   ← si modulo_repuestos
```

### 4.2 Workspace Home

**Archivo a modificar:** `templates/taller/common/workspace_home.html`

Actualmente muestra tres tarjetas fijas (Vehículos, Documentos, Desarme) para todos. Objetivo:

```html
{% if modulos_activos.taller %}
  <a href="{% country_url 'vehiculos:lista_vehiculos' %}">🚗 Vehículos en taller</a>
{% endif %}
<a href="{{ base }}/documentos/">📄 Documentos</a>  {# siempre #}
{% if modulos_activos.desarmaduria %}
  <a href="{% country_url 'desarme:lista_vehiculos' %}">🧩 Patio de desarme</a>
{% endif %}
{% if modulos_activos.repuestos %}
  <a href="{% country_url 'repuestos:catalogo' %}">📦 Catálogo</a>
{% endif %}
```

### 4.3 Accesos Rápidos por Vertical

| Vertical | Acceso rápido principal | KPI principal |
|---|---|---|
| Taller | Nueva OT | OTs abiertas / técnicos activos |
| Desarmaduría | Nuevo vehículo de desarme | Piezas disponibles / recuperación % |
| Casa de Repuestos | Nueva entrada de stock | Valor inventario / SKUs bajo mínimo |

---

## 5. Onboarding

### 5.1 Flujo Objetivo

```
/accounts/signup/
    ↓
  Crear User + Empresa
    ↓
/onboarding/identidad/
  campos: nombre_taller, logo
  NUEVO: selector de tipo de negocio
  ─────────────────────────────────
  ¿Qué tipo de negocio administras?
  ○ Taller mecánico o servicio automotriz
  ○ Desarmaduría / Reciclaje automotriz
  ○ Casa de repuestos / Autopartes
  ○ Más de uno (multivertical)
    ↓
  Se guarda en ConfiguracionEmpresa:
    - rubro_principal = "WORKSHOP" | "MIXED" | "PARTS"
    - modulo_taller = True/False
    - modulo_desarmaduria = True/False
    - modulo_repuestos = True/False
    ↓
/onboarding/finalizar/
  (igual al actual)
    ↓
  Redirigir al Dashboard correspondiente a la vertical
```

### 5.2 Defaults por Selección

| Selección usuario | rubro_principal | modulo_taller | modulo_desarmaduria | modulo_repuestos |
|---|---|---|---|---|
| Taller | WORKSHOP | True | False | False |
| Desarmaduría | MIXED | False | True | True |
| Casa de Repuestos | PARTS | False | False | True |
| Multivertical | MIXED | True | True | True |

**Retrocompatibilidad:** Las empresas existentes sin ningún módulo guardado asumen `True` en los tres (campo `default=True`). El comportamiento actual no cambia.

### 5.3 Cambios en Archivos

| Archivo | Cambio |
|---|---|
| `taller/forms/onboarding.py` | Agregar campo `tipo_negocio` (ChoiceField no-modelo) |
| `templates/onboarding/paso_identidad.html` | Agregar selector de vertical (4 opciones con íconos) |
| `taller/views/onboarding_views.py:onboarding_guardar_paso` | Mapear `tipo_negocio` → flags de módulo |
| `taller/services/company_defaults_service.py` | Método `apply_modulos_por_tipo()` |

---

## 6. Portal Público y SEO

### 6.1 Estructura de URLs Públicas

```python
# gestion_taller/urls.py o taller/urls_public.py

urlpatterns += [
    # Landings por vertical (sin prefijo de país — SEO global)
    path("talleres/", views.landing_talleres, name="landing_talleres"),
    path("desarmadurias/", views.landing_desarmadurias, name="landing_desarmadurias"),
    path("repuestos/", views.landing_repuestos, name="landing_repuestos"),

    # Landings con prefijo de país (para SEO local)
    path("cl/es/talleres/", views.landing_talleres_cl, name="landing_talleres_cl"),
    path("cl/es/desarmadurias/", views.landing_desarmadurias_cl, name="landing_desarmadurias_cl"),
    path("us/en/workshops/", views.landing_talleres_us, name="landing_talleres_us"),
    path("us/en/salvage-yards/", views.landing_desarmadurias_us, name="landing_desarmadurias_us"),
    path("us/es/desarmadurias/", views.landing_desarmadurias_us_es, name="landing_desarmadurias_us_es"),
]
```

### 6.2 Jerarquía de Templates de Landing

```
templates/public/
├── landing_talleres.html
├── landing_desarmadurias.html
├── landing_repuestos.html
├── landing_chile_completa.html   ← existente, no tocar
└── base_landing.html             ← base común para las tres landings nuevas
```

### 6.3 Estrategia SEO

Cada landing tiene:
- `<title>` específico para la vertical.
- `<meta name="description">` con la propuesta de valor de esa vertical.
- `<h1>` con la keyword principal.
- Open Graph con imagen representativa de cada vertical.
- Schema.org `SoftwareApplication` con `applicationCategory` diferenciado.
- `<link rel="canonical">` para evitar duplicación entre variantes de idioma.

**Keywords objetivo por vertical:**

| Vertical | CL | US-ES | US-EN |
|---|---|---|---|
| Talleres | "software taller mecánico Chile" | "software taller mecánico USA" | "auto shop management software" |
| Desarmadurías | "software desarmaduría Chile" | "software deshuesadero USA" | "salvage yard software" / "junkyard software" |
| Repuestos | "software casa de repuestos Chile" | "software refaccionaria" | "auto parts store software" |

### 6.4 Historia de Atlanta en /desarmadurias/

La landing de desarmadurías incluye obligatoriamente:

```html
<section class="historia-fundador">
  <h2>Hecho por alguien que conoce el negocio por dentro</h2>
  <p>
    Más de 20 años trabajando en talleres y desarmadurías en Atlanta, Georgia.
    Después de vivir el desorden del inventario, decidí crear el sistema
    que siempre necesité. Hoy eGarage ayuda a administrar vehículos,
    piezas, ventas e inventario desde un solo lugar.
  </p>
  <p class="caso-real">
    Atlanta Reciclajes SPA — el negocio donde eGarage se usa todos los días.
  </p>
</section>
```

Esto no es marketing genérico. Es un diferenciador que ningún competidor puede copiar.

---

## 7. Vertical Talleres — Especificación Técnica

### 7.1 Estado actual

Aproximadamente 80% completo para el flujo principal. No requiere construcción nueva.

### 7.2 Componentes del Core que pertenecen a Taller

| Componente | Tabla | ¿Exclusivo Taller? |
|---|---|---|
| Técnico/Mecánico | `taller_tecnico` | Sí |
| Servicio | `taller_servicio` (servicios/) | Sí |
| Cita | `taller_cita` | Sí |
| InspeccionIngreso | `taller_inspeccioningreso` | Sí |
| Kilometraje | `taller_kilometraje` | Sí |
| Vehículo (cliente/reparación) | `taller_vehiculo` | Compartido |
| Documento (OT/cotización) | `taller_documento` | Compartido |
| Repuesto (consumo en OT) | `taller_repuesto` | Compartido |

### 7.3 Accesos rápidos del workspace Taller

- Nueva OT
- Nueva cotización
- Vehículos en proceso
- Agenda del día
- Repuestos con stock bajo

### 7.4 Dashboard Taller

- OTs abiertas / cerradas / en espera
- Producción por técnico
- Repuestos más utilizados
- Tiempo promedio de reparación

---

## 8. Vertical Desarmadurías — Especificación Técnica

### 8.1 Estado actual

Aproximadamente 75% completo. Los modelos, vistas y templates principales existen. Falta: gate de acceso, onboarding especializado, landing propia.

### 8.2 Componentes exclusivos de Desarmaduría

| Componente | Tabla | Archivo |
|---|---|---|
| VehiculoDesarme | `taller_vehiculodesarme` | `models/vehiculo_desarme.py` |
| PiezaDesarme | `taller_piezadesarme` | `models/pieza_desarme.py` |
| VentaDesarme | `taller_ventadesarme` | `models/venta_desarme.py` |
| VendedorDesarme | `taller_vendedordesarme` | `models/vendedor_desarme.py` |
| InterchangePieza | `taller_interchangepieza` | `models/interchange_pieza.py` |
| VehiculoFinancialSnapshot | `taller_vehiculofinancialsnapshot` | `models/vehiculo_financial.py` |
| VehicleFinancialEvent | `taller_vehiclefinancialevent` | `models/vehiculo_financial.py` |
| CatalogoRepuestoEmpresa | `taller_catalogorepuestoempresa` | `models/catalogo_repuesto_empresa.py` |

### 8.3 Flujo operativo principal

```
1. Ingresar vehículo de desarme (VehiculoDesarme)
      ↓
2. Revisar y registrar daños por zona (carrocería, motor, etc.)
      ↓
3. Desarmar → crear piezas (PiezaDesarme) con código, precio, condición
      ↓
4. Las piezas aparecen en el inventario
      ↓
5. Cliente llega o busca en kiosco → iniciar venta
      ↓
6. Confirmar venta → se genera VentaDesarme + descuenta stock
      ↓
7. Si hay documento → generar desde Documento (integración con core)
      ↓
8. Finanzas: VehicleFinancialEvent registra cada ingreso/egreso del vehículo
      ↓
9. VehiculoFinancialSnapshot consolida ROI, recuperación %, health score
```

### 8.4 Accesos rápidos del workspace Desarmaduría

- Nuevo vehículo de desarme
- Inventario (piezas disponibles)
- Venta rápida
- Dashboard financiero del patio
- Kiosco (vista pública)

### 8.5 Dashboard Desarmaduría

- Piezas disponibles / vendidas / en scrap
- Vehículos por estado (INGRESADO, DESARMANDO, DESARMADO, AGOTADO)
- ROI promedio del patio
- Top 5 vehículos con mayor recuperación
- Top 5 piezas más vendidas
- Ingresos vs. inversión (timeline)

---

## 9. Vertical Casa de Repuestos — Especificación Técnica

### 9.1 Estado actual

Aproximadamente 15% completo. El modelo `Repuesto` existe pero fue diseñado para consumo en OTs, no para administración de inventario de una casa de repuestos.

### 9.2 Componentes a construir

#### Modelo Proveedor

```python
class Proveedor(TenantScoped):
    nombre = models.CharField(max_length=200)
    rut = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=40, blank=True)
    direccion = models.CharField(max_length=200, blank=True)
    condicion_pago = models.CharField(
        max_length=20,
        choices=[("CONTADO", "Contado"), ("CREDITO_30", "30 días"), ("CREDITO_60", "60 días")],
        default="CONTADO",
    )
    activo = models.BooleanField(default=True)

    class Meta(TenantScoped.Meta):
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
```

#### Modelo OrdenCompra

```python
class OrdenCompra(TenantScoped):
    numero = models.PositiveIntegerField()
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT)
    fecha = models.DateField(auto_now_add=True)
    estado = models.CharField(
        choices=[
            ("BORRADOR", "Borrador"),
            ("ENVIADA", "Enviada al proveedor"),
            ("RECIBIDA_PARCIAL", "Recibida parcialmente"),
            ("RECIBIDA_TOTAL", "Recibida completa"),
            ("ANULADA", "Anulada"),
        ],
        default="BORRADOR",
    )
    observaciones = models.TextField(blank=True)
```

#### Modelo LineaOrdenCompra

```python
class LineaOrdenCompra(models.Model):
    orden = models.ForeignKey(OrdenCompra, on_delete=models.CASCADE, related_name="lineas")
    repuesto = models.ForeignKey("taller.Repuesto", on_delete=models.PROTECT)
    cantidad_pedida = models.PositiveIntegerField()
    cantidad_recibida = models.PositiveIntegerField(default=0)
    precio_costo = models.DecimalField(max_digits=12, decimal_places=2)
```

#### Modelo MovimientoStock

```python
class MovimientoStock(TenantScoped):
    repuesto = models.ForeignKey("taller.Repuesto", on_delete=models.PROTECT)
    tipo = models.CharField(
        choices=[
            ("ENTRADA_COMPRA", "Entrada por compra"),
            ("SALIDA_VENTA", "Salida por venta"),
            ("SALIDA_OT", "Salida por OT"),
            ("AJUSTE_POS", "Ajuste positivo"),
            ("AJUSTE_NEG", "Ajuste negativo"),
            ("DEVOLUCION", "Devolución"),
        ]
    )
    cantidad = models.IntegerField()  # positivo=entrada, negativo=salida
    stock_antes = models.IntegerField()
    stock_despues = models.IntegerField()
    referencia_id = models.IntegerField(null=True, blank=True)
    referencia_tipo = models.CharField(max_length=20, blank=True)  # "OrdenCompra", "Documento", etc.
    fecha = models.DateTimeField(auto_now_add=True)
```

### 9.3 Relación con Repuesto existente

El modelo `Repuesto` actual (`taller/models/repuesto.py`) se **reutiliza** para la vertical Casa de Repuestos. No se duplica.

La diferencia es el **flujo que lo alimenta:**
- En Talleres: el stock de Repuesto baja cuando se crea una línea en un Documento (OT).
- En Casa de Repuestos: el stock sube por `MovimientoStock` tipo `ENTRADA_COMPRA` y baja por `SALIDA_VENTA` o `SALIDA_OT`.

### 9.4 Flujo operativo objetivo

```
1. Registrar proveedor (Proveedor)
      ↓
2. Crear orden de compra → seleccionar productos (OrdenCompra + LineaOrdenCompra)
      ↓
3. Recibir mercadería → crear MovimientoStock tipo ENTRADA_COMPRA
   → actualiza cantidad_stock en Repuesto
      ↓
4. Cliente llega o busca en catálogo
      ↓
5. Venta directa → crear MovimientoStock tipo SALIDA_VENTA
   → descuenta stock → genera Documento (tipo BOLETA/FACTURA)
      ↓
6. Dashboard: rentabilidad por SKU, rotación, SKUs bajo mínimo
```

### 9.5 Dashboard Casa de Repuestos

- Valor total del inventario (precio_costo × stock)
- SKUs bajo stock mínimo
- Órdenes de compra pendientes
- Ventas del mes vs. mes anterior
- Top 10 SKUs por rotación
- Margen bruto por categoría

---

## 10. Estrategia de Migración

### 10.1 Principio

Ninguna migración rompe producción. Cada migración es aditiva o tiene un `default` que mantiene el comportamiento actual.

### 10.2 Tabla de Migraciones Planificadas

| # | Nombre | Tipo | Riesgo | Backfill |
|---|---|---|---|---|
| M-01 | `add_modulos_configuracion` | ADD COLUMN × 3 en ConfiguracionEmpresa | Ninguno | No (default=True) |
| M-02 | `add_proveedor` | CREATE TABLE Proveedor | Ninguno | No |
| M-03 | `add_orden_compra` | CREATE TABLE OrdenCompra + Linea | Ninguno | No |
| M-04 | `add_movimiento_stock` | CREATE TABLE MovimientoStock | Ninguno | No |
| M-05 | `backfill_modulos_por_rubro` | UPDATE ConfiguracionEmpresa | Bajo | Sí — basado en rubro_principal |

**M-05 detalle:**
```sql
-- Empresas con rubro_principal PARTS → solo módulo repuestos
UPDATE configuracionempresa SET modulo_taller=False, modulo_desarmaduria=False WHERE rubro_principal='PARTS';
-- No tocar el resto: ya tienen default=True en los tres
```

### 10.3 Empresas Existentes

Las empresas actualmente en producción no se verán afectadas hasta que se ejecute M-05. Incluso después de M-05, el único efecto será que las empresas configuradas como `PARTS` no verán el módulo de taller en el menú — lo que ya es correcto.

### 10.4 Rollback por Etapa

| Etapa | Rollback |
|---|---|
| 0 (landings) | Eliminar los 3-4 archivos nuevos |
| 1 (migración flags) | `manage.py migrate taller XXXX` hacia atrás + revertir forms/templates onboarding |
| 2 (menú condicional) | Revertir 1 archivo: `templates/base.html` |
| 3 (decorator en views) | Revertir los `@requiere_modulo` de las vistas |
| 4 (onboarding especializado) | Revertir template + form |
| 5 (vertical repuestos) | Eliminar modelos nuevos + migraciones (sin datos en prod aún) |

---

## 11. Convenciones de Código

### 11.1 Nombres de variables en templates

```html
{# CORRECTO: usar context processor #}
{% if modulos_activos.desarmaduria %}

{# EVITAR: acceso directo al modelo desde template #}
{% if empresa.config.modulo_desarmaduria %}
```

### 11.2 Verificación de módulo en vistas

```python
# CORRECTO
@login_required
@requiere_modulo("DESARMADURIA")
def lista_vehiculos(request):
    ...

# TAMBIÉN CORRECTO para CBVs
class VehiculoDesarmeListView(RequiereModuloMixin, LoginRequiredMixin, TenantViewMixin, ListView):
    modulo_requerido = "DESARMADURIA"
    ...

# INCORRECTO: verificar en lógica de negocio
def lista_vehiculos(request):
    if not request.empresa.config.modulo_desarmaduria:
        return 403
    ...
```

### 11.3 Defaults seguros

Cualquier acceso a flags de módulo debe tener un `getattr(..., True)` como fallback para no romper con empresas que aún no tienen `ConfiguracionEmpresa`:

```python
config = getattr(empresa, "config", None)
modulo_activo = getattr(config, "modulo_desarmaduria", True) if config else True
```

---

## 12. Resumen de Decisiones Arquitectónicas

| Decisión | Elección | Alternativa descartada |
|---|---|---|
| ¿Cómo modelar módulos? | Flags booleanos en ConfiguracionEmpresa (Etapa 1) | Tabla EmpresaModulo (reservada para Etapa 5+) |
| ¿Default para empresas existentes? | `default=True` en los tres módulos | `default=False` con backfill previo (riesgo innecesario) |
| ¿Tipo de campo en onboarding? | ChoiceField no-modelo, se mapea a flags en save() | Campo modelo directo en Empresa |
| ¿Protección por URL? | Decorator `@requiere_modulo` en vistas | Middleware (afecta toda la cadena) |
| ¿Menú diferenciado? | Condicionales en templates (variables del context processor) | Tres templates de base distintos |
| ¿Dashboards? | Un dashboard base con secciones condicionales | Tres dashboards independientes |
| ¿Landings públicas? | Rutas globales `/talleres/`, `/desarmadurias/`, `/repuestos/` + variantes por país | Solo variantes por país |
| ¿Casa de Repuestos en Etapa 1? | No. Solo landings y flags. Construir en Etapa 5+ | Construir todo de una vez (alto riesgo) |
| ¿Dividir repositorio? | No. Una sola app. | Tres repos / tres deploys |
| ¿Nueva app Django para cada vertical? | No. Sub-paquetes dentro de `taller/`. | Nuevas Django apps (impacto en URLs, migrations, settings) |

---

*Este documento es la guía de arquitectura. Ningún cambio de código se realiza hasta que este documento sea aprobado. Ver ROADMAP_VERTICALS.md para el plan de implementación por fases.*
