# eGarage — Arquitectura de Productos V1
**Versión:** 2.0  
**Fecha:** 2026-07-28  
**Estado:** Pendiente de aprobación  
**Rama:** feature/vertical-architecture-v1  
**Auditoría base:** docs/auditorias/auditoria_final_verticales_egarage.md  
**Cambios desde V1.0:** Modelo normalizado EmpresaModulo · reorden auth antes de menú · rubro desacoplado de módulos · MenuService · nomenclatura de productos

---

## Principios de Diseño

1. **Una sola aplicación.** Un repositorio, un servidor, una base de datos, una autenticación, un despliegue.
2. **Cambios incrementales.** Cada etapa es independiente, reversible y verificable antes de la siguiente.
3. **Retrocompatibilidad total.** Las empresas existentes no notan ningún cambio de comportamiento hasta que se configuren explícitamente.
4. **Autorización en backend antes que visibilidad en frontend.** Las URLs se protegen antes de que el menú las oculte — nunca al revés.
5. **`rubro_principal` es identidad; `EmpresaModulo` es acceso.** Son dimensiones independientes. Una empresa puede ser `WORKSHOP` (identidad) pero tener el producto Salvage habilitado (acceso). No se mezclan.
6. **El menú lo construye un servicio, no un template.** Los templates iteran sobre una lista. La lógica vive en `MenuService`.
7. **Tres productos, no tres verticales.** eGarage Workshop, eGarage Salvage, eGarage Parts. Son nombres de producto, no categorías internas.

---

## Nomenclatura de Productos

eGarage se posiciona externamente como tres productos dentro de una misma plataforma:

| Código interno | Nombre de producto | Mercado objetivo | URL pública |
|---|---|---|---|
| `WORKSHOP` | eGarage Workshop | Talleres mecánicos, vulcanizaciones, llanteras, carwash, pintura | `/talleres/` · `/us/en/workshops/` |
| `SALVAGE` | eGarage Salvage | Desarmadurías, recicladores automotrices, patios de chatarra | `/desarmadurias/` · `/us/en/salvage-yards/` · `/us/es/deshuesaderos/` |
| `PARTS` | eGarage Parts | Casas de repuestos, refaccionarias, distribuidores de autopartes | `/repuestos/` · `/us/en/auto-parts/` |

Los tres productos corren en la misma aplicación Django. No hay repos separados, no hay bases de datos separadas, no hay deploys separados.

**El código interno (`WORKSHOP`, `SALVAGE`, `PARTS`) es el vocabulario canónico usado en modelos, servicios y tests. Los nombres de producto son solo para el portal público y el onboarding.**

---

## Modelo Mental

```
eGarage Platform
│
├── Portal Público
│   ├── /                       → selector de producto o landing general
│   ├── /talleres/              → eGarage Workshop
│   ├── /desarmadurias/         → eGarage Salvage
│   ├── /repuestos/             → eGarage Parts
│   └── /us/en/...              → variantes en inglés
│
├── Core (compartido por los tres productos)
│   ├── Empresa (tenant raíz)
│   ├── ConfiguracionEmpresa (rubro_principal, feature flags de UI)
│   ├── EmpresaModulo (WORKSHOP / SALVAGE / PARTS — autorización)
│   ├── MenuService (construye el menú según EmpresaModulo)
│   ├── Usuario / TeamMember
│   ├── Cliente
│   ├── Vehículo (cliente/reparación)
│   ├── Documento (cotización / OT / boleta)
│   ├── Impuestos
│   ├── Suscripción / Plan
│   ├── Auditoría
│   └── Notificaciones
│
├── Producto Workshop (eGarage Workshop)
│   ├── Técnicos / Mecánicos
│   ├── Servicios
│   ├── Órdenes de Trabajo
│   ├── Cotizaciones
│   ├── Citas / Agenda
│   ├── Inspección de ingreso
│   ├── Historial del vehículo
│   └── Repuestos (consumo en OT)
│
├── Producto Salvage (eGarage Salvage)
│   ├── VehiculoDesarme
│   ├── PiezaDesarme
│   ├── VentaDesarme
│   ├── VendedorDesarme
│   ├── Interchange
│   ├── Kiosco público
│   ├── Ciclo de vida del vehículo
│   └── Finanzas por vehículo (snapshot, eventos)
│
└── Producto Parts (eGarage Parts)
    ├── Proveedor (ficha completa)
    ├── OrdenCompra + LineaOrdenCompra
    ├── RecepcionMercaderia
    ├── MovimientoStock
    ├── Bodega
    ├── VentaRepuesto (directa, sin OT)
    └── Dashboard de rentabilidad por SKU
```

---

## 1. `rubro_principal` vs `EmpresaModulo` — Separación de Responsabilidades

Esta es la decisión de diseño más importante de esta arquitectura. Las dos dimensiones son independientes y no deben mezclarse.

### `rubro_principal` — Identidad del negocio

**Archivo:** `taller/models/configuracion.py:166`  
**Propósito:** Describe qué tipo de negocio es la empresa. Controla presentación y UX.

```
rubro_principal → WORKSHOP | TIRE | BODYSHOP | ELECTRIC | PARTS | EXHAUST | ...
```

**Efectos actuales (no se tocan):**
- Etiqueta del campo "responsable" en documentos (`rubros_responsables.py`)
- Secciones visibles en el formulario de OT (`get_secciones_visibles()`)
- Roles permitidos para técnicos (`rubros_logic.py`)

**Efectos futuros a agregar:**
- Texto del onboarding ("tu taller" / "tu desarmaduría" / "tu bodega")
- Copy del email de bienvenida
- Nombre del "responsable" en documentos impresos
- Datos de demo al finalizar onboarding

**Lo que `rubro_principal` NUNCA controla:**
- Qué URLs son accesibles
- Qué aparece en el menú
- Qué módulos están habilitados

### `EmpresaModulo` — Acceso a productos

**Archivo futuro:** `taller/models/empresa_modulo.py`  
**Propósito:** Define a qué productos tiene acceso la empresa. Controla autorización.

```
EmpresaModulo → WORKSHOP | SALVAGE | PARTS (uno o varios por empresa)
```

**Efectos:**
- Qué URLs el decorator `@requiere_producto` permite
- Qué secciones construye `MenuService`
- Qué tarjetas muestra el workspace
- Qué sección del dashboard se activa

**Lo que `EmpresaModulo` NUNCA controla:**
- Etiquetas en documentos
- Formularios de OT
- El nombre del responsable

### Ejemplo: empresa multiproducto

```python
# Una empresa puede ser "Taller de mecánica" (rubro_principal=WORKSHOP)
# pero también tener acceso al producto Salvage porque también desarma:

empresa.config.rubro_principal = "WORKSHOP"       # identidad: "somos un taller"
empresa.modulos.values_list("codigo", flat=True)  # acceso: ["WORKSHOP", "SALVAGE"]
```

---

## 2. Modelo `EmpresaModulo` — Diseño Definitivo

Este es el modelo canónico desde el día 1. No se usa como paso intermedio; es la arquitectura permanente.

**Archivo futuro:** `taller/models/empresa_modulo.py`

```python
from django.db import models


PRODUCTO_CHOICES = [
    ("WORKSHOP", "eGarage Workshop"),
    ("SALVAGE",  "eGarage Salvage"),
    ("PARTS",    "eGarage Parts"),
]


class EmpresaModulo(models.Model):
    """
    Registra qué productos eGarage tiene habilitados una empresa.
    Cada fila = un producto activo. Ausencia de fila = producto no habilitado.
    """
    empresa = models.ForeignKey(
        "taller.Empresa",
        on_delete=models.CASCADE,
        related_name="modulos",
    )
    codigo = models.CharField(max_length=20, choices=PRODUCTO_CHOICES)
    activo = models.BooleanField(default=True)
    activado_en = models.DateTimeField(auto_now_add=True)
    activado_por = models.ForeignKey(
        "auth.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        verbose_name = "Módulo de empresa"
        verbose_name_plural = "Módulos de empresa"
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "codigo"],
                name="uq_empresa_modulo_codigo",
            )
        ]
        indexes = [
            models.Index(fields=["empresa", "activo"]),
        ]

    def __str__(self):
        estado = "activo" if self.activo else "inactivo"
        return f"{self.empresa_id} · {self.codigo} ({estado})"
```

### Por qué tabla normalizada y no booleanos en `ConfiguracionEmpresa`

| Criterio | Booleanos en Config | Tabla EmpresaModulo |
|---|---|---|
| Agregar un cuarto producto en el futuro | Requiere nueva migración y nuevo booleano | Solo nuevo choice en `PRODUCTO_CHOICES` |
| Auditoría: ¿quién activó el módulo y cuándo? | Imposible sin campos extra | `activado_en` + `activado_por` ya están |
| Desactivar temporalmente un módulo | Requiere modificar un campo en Config | Setear `activo=False` en la fila |
| Consultar empresas que usan Salvage | `ConfiguracionEmpresa.objects.filter(modulo_desarmaduria=True)` | `EmpresaModulo.objects.filter(codigo="SALVAGE", activo=True)` |
| Agregar metadata por módulo (fecha límite, plan, notas) | Requiere campos extra en Config | Nuevos campos en EmpresaModulo |
| Riesgo de crecer `ConfiguracionEmpresa` que ya tiene 20+ campos | Alto | Ninguno: tabla separada |
| Complejidad inicial | Menor | Marginalmente mayor |

La única ventaja de los booleanos es menor complejidad inicial. No es suficiente para justificar una arquitectura que bloquea el crecimiento.

### Helper en `Empresa`

Para que el código de vistas y servicios sea limpio, se agrega un helper en el modelo `Empresa`:

```python
# taller/models/empresa.py — método a agregar

def tiene_producto(self, codigo: str) -> bool:
    """Verifica si la empresa tiene un producto eGarage habilitado."""
    return self.modulos.filter(codigo=codigo, activo=True).exists()

def productos_activos(self) -> list[str]:
    """Devuelve la lista de códigos de productos activos."""
    return list(self.modulos.filter(activo=True).values_list("codigo", flat=True))
```

### Retrocompatibilidad con empresas existentes

La migración que crea `EmpresaModulo` incluye un backfill que crea filas para todas las empresas existentes:

```python
# En la migración:
def backfill_modulos(apps, schema_editor):
    Empresa = apps.get_model("taller", "Empresa")
    EmpresaModulo = apps.get_model("taller", "EmpresaModulo")
    for empresa in Empresa.objects.all():
        # Todas las empresas existentes reciben los tres productos
        # para no cambiar ningún comportamiento activo en producción
        for codigo in ["WORKSHOP", "SALVAGE", "PARTS"]:
            EmpresaModulo.objects.get_or_create(empresa=empresa, codigo=codigo)
```

Las empresas nuevas reciben solo los productos que elijan en el onboarding.

---

## 3. Sistema de Autorización — `@requiere_producto`

### Decorator para FBVs

**Archivo futuro:** `taller/decorators.py`

```python
from functools import wraps
from django.http import HttpResponseForbidden, JsonResponse


def requiere_producto(codigo: str):
    """
    Verifica que la empresa tenga habilitado un producto eGarage.

    Uso:
        @login_required
        @requiere_producto("SALVAGE")
        def lista_vehiculos_desarme(request): ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            empresa = getattr(request, "empresa", None)
            if empresa is None:
                from django.shortcuts import redirect
                return redirect("account_login")

            if not empresa.tiene_producto(codigo):
                if _is_api_request(request):
                    return JsonResponse(
                        {"error": f"Producto {codigo} no habilitado", "codigo": codigo},
                        status=403,
                    )
                return HttpResponseForbidden(
                    f"Tu empresa no tiene acceso al producto {codigo}."
                )
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def _is_api_request(request) -> bool:
    return (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or "application/json" in request.headers.get("Accept", "")
        or "/api/" in request.path
    )
```

### Mixin para CBVs

```python
# taller/mixins.py — agregar junto a los mixins existentes

class RequiereProductoMixin:
    """
    Mixin para Class-Based Views.

    Uso:
        class VehiculoDesarmeListView(RequiereProductoMixin, LoginRequiredMixin, ...):
            producto_requerido = "SALVAGE"
    """
    producto_requerido: str = None

    def dispatch(self, request, *args, **kwargs):
        if self.producto_requerido:
            empresa = getattr(request, "empresa", None)
            if empresa is None or not empresa.tiene_producto(self.producto_requerido):
                from django.http import HttpResponseForbidden
                return HttpResponseForbidden("Producto no habilitado.")
        return super().dispatch(request, *args, **kwargs)
```

### Aplicación por producto

| Producto | Vistas a decorar |
|---|---|
| SALVAGE | Todas las FBVs/CBVs en `taller/desarme/views.py`, `views_venta.py`, `views_inventario.py`, `views_pdf.py` |
| PARTS | Vistas nuevas de la Épica E5 (Proveedor, OrdenCompra, MovimientoStock) |
| WORKSHOP | Sin decorator en etapas iniciales — es el producto por defecto |

**Nunca se decora:**
- Vistas del núcleo compartido (Documentos, Clientes, Vehículos de reparación)
- Kiosco público (`/tienda/<slug>/`) — es acceso público sin empresa autenticada
- Vistas del admin de Django

### Orden obligatorio de decoradores

```python
@login_required            # primero: ¿está autenticado?
@requiere_producto("SALVAGE")  # segundo: ¿tiene el producto?
def lista_vehiculos(request):
    ...
```

---

## 4. `MenuService` — Construcción Centralizada del Menú

El menú no se construye con condicionales en los templates. Los templates iteran sobre una lista de items que devuelve un servicio Python. Toda la lógica vive en el servicio.

### Por qué un servicio y no condicionales en templates

| Aspecto | Condicionales en template | MenuService |
|---|---|---|
| Testear la lógica del menú | Requiere render completo | Test unitario puro |
| Agregar un item nuevo | Editar base.html (archivo crítico) | Editar MenuService (archivo contenido) |
| Reutilizar el menú en API, email, mobile | Imposible directamente | `MenuService.build_for(empresa)` desde cualquier código |
| Auditar qué ve cada empresa | Difícil de razonar en HTML | Inspección directa del objeto retornado |

### Diseño del servicio

**Archivo futuro:** `taller/services/menu_service.py`

```python
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MenuItem:
    label_es: str
    label_en: str
    icon: str
    url_name: str           # nombre de URL de Django (para {% url %} o reverse())
    url_args: dict = field(default_factory=dict)
    grupo: str = "core"     # "core" | "workshop" | "salvage" | "parts"
    requires_owner: bool = False


class MenuService:
    """
    Construye la lista de ítems de menú para una empresa.
    Ningún template contiene lógica de qué mostrar; solo iteran esta lista.
    """

    # Ítems del núcleo: siempre presentes para cualquier empresa autenticada
    CORE_ITEMS: list[MenuItem] = [
        MenuItem("Ajustes",     "Settings",  "⚙️",  "company_settings",  grupo="core"),
        MenuItem("Equipo",      "Team",      "👤",  "team",              grupo="core", requires_owner=True),
        MenuItem("Centro",      "Center",    "🚀",  "centro_operaciones",grupo="core"),
        MenuItem("Clientes",    "Clients",   "👥",  "clientes:lista_clientes",  grupo="core"),
        MenuItem("Documentos",  "Documents", "📄",  "documentos:lista_documentos", grupo="core"),
        MenuItem("Reportes",    "Reports",   "📊",  "reportes:reportes_dashboard", grupo="core"),
    ]

    WORKSHOP_ITEMS: list[MenuItem] = [
        MenuItem("Vehículos",  "Vehicles", "🚗", "vehiculos:lista_vehiculos", grupo="workshop"),
        MenuItem("Servicios",  "Services", "🛠️", "servicios:servicios_menu",  grupo="workshop"),
        MenuItem("Repuestos",  "Parts",    "🔧", "repuestos:lista_repuestos", grupo="workshop"),
        MenuItem("Extra",      "Extra",    "⭐", "servicios:otros_servicios", grupo="workshop"),
    ]

    SALVAGE_ITEMS: list[MenuItem] = [
        MenuItem("Desarme",       "Salvage",       "🧩", "desarme:index",          grupo="salvage"),
        MenuItem("Interchange",   "Interchange",   "🔍", "desarme:lista_interchange", grupo="salvage"),
        MenuItem("Kiosco",        "Storefront",    "🏪", "tienda:tienda_publica",   grupo="salvage"),
    ]

    PARTS_ITEMS: list[MenuItem] = [
        MenuItem("Catálogo",    "Catalog",   "📦", "parts:catalogo",    grupo="parts"),
        MenuItem("Proveedores", "Suppliers", "🚚", "parts:proveedores",  grupo="parts"),
        MenuItem("Compras",     "Purchases", "📥", "parts:compras",      grupo="parts"),
    ]

    @classmethod
    def build_for(cls, empresa, user=None) -> list[MenuItem]:
        """
        Retorna la lista completa de ítems de menú para la empresa.
        Respeta el estado de autenticación y los productos habilitados.
        """
        items: list[MenuItem] = []

        # Núcleo: siempre presente
        for item in cls.CORE_ITEMS:
            if item.requires_owner and user and not _is_owner(user):
                continue
            items.append(item)

        # Productos opcionales
        if empresa and empresa.tiene_producto("WORKSHOP"):
            items.extend(cls.WORKSHOP_ITEMS)

        if empresa and empresa.tiene_producto("SALVAGE"):
            items.extend(cls.SALVAGE_ITEMS)

        if empresa and empresa.tiene_producto("PARTS"):
            items.extend(cls.PARTS_ITEMS)

        return items

    @classmethod
    def build_groups_for(cls, empresa, user=None) -> dict[str, list[MenuItem]]:
        """
        Retorna el menú agrupado por sección, útil para templates con filas separadas.
        """
        items = cls.build_for(empresa, user)
        groups: dict[str, list[MenuItem]] = {}
        for item in items:
            groups.setdefault(item.grupo, []).append(item)
        return groups
```

### Integración con el Context Processor

```python
# taller/context_processors/empresa_contexto.py — versión actualizada

from taller.services.menu_service import MenuService

def empresa_contexto(request):
    if not request.user.is_authenticated:
        return {"empresa": None, "menu_items": [], "menu_groups": {}}
    try:
        empresa = request.user.empresa
        menu_groups = MenuService.build_groups_for(empresa, user=request.user)
        return {
            "empresa": empresa,
            "nombre_taller": getattr(empresa, "nombre_taller", "eGarage"),
            "menu_groups": menu_groups,
        }
    except Exception:
        return {"empresa": None, "menu_items": [], "menu_groups": {}}
```

### Template base — sin condicionales de lógica

```html
{# templates/base.html — sección de navegación #}
{# El template solo itera; no decide qué mostrar #}

<nav id="main-navigation">
  {% for grupo, items in menu_groups.items %}
    <div class="nav-group nav-group--{{ grupo }}">
      {% for item in items %}
        <a href="{% country_url item.url_name %}" class="nav-button-standard">
          <span class="nav-icon">{{ item.icon }}</span>
          <span class="nav-text">
            {% if request.path|slice:":4" == "/us/" %}{{ item.label_en }}{% else %}{{ item.label_es }}{% endif %}
          </span>
        </a>
      {% endfor %}
    </div>
  {% endfor %}
</nav>
```

---

## 5. Onboarding

### Separación de responsabilidades en el onboarding

El onboarding captura dos cosas distintas:

1. **Identidad** → escribe en `ConfiguracionEmpresa.rubro_principal`  
   *"¿Qué tipo de negocio eres?"* — Workshop, Salvage, Parts

2. **Acceso inicial** → crea filas en `EmpresaModulo`  
   *"¿Qué productos de eGarage quieres activar?"* — derivado de la identidad, pero ajustable

El administrador puede luego activar o desactivar productos en `EmpresaModulo` sin cambiar el `rubro_principal`.

### Flujo objetivo

```
/accounts/signup/
    ↓
  Crear User + Empresa (vía allauth + CountryAwareAccountAdapter)
    ↓
/onboarding/identidad/   (paso 1)
  campos: nombre_taller, logo
  NUEVO: selector de producto
  ─────────────────────────────────────────────────
  ¿Qué administras con eGarage?

  [🔧 Taller / Servicios automotrices]
     → rubro_principal = WORKSHOP
     → EmpresaModulo: WORKSHOP

  [🧩 Desarmaduría / Reciclaje automotriz]
     → rubro_principal = SALVAGE (nuevo choice a agregar)
     → EmpresaModulo: SALVAGE + PARTS (opcional)

  [📦 Casa de repuestos / Autopartes]
     → rubro_principal = PARTS
     → EmpresaModulo: PARTS

  [🔀 Más de uno]
     → rubro_principal = MIXED
     → EmpresaModulo: WORKSHOP + SALVAGE + PARTS
  ─────────────────────────────────────────────────
    ↓
/onboarding/finalizar/   (paso 3)
  Template elegido según rubro_principal
  Demo data cargada según EmpresaModulo activos
    ↓
  empresa.onboarding_completado = True
    ↓
  redirect → dashboard adaptado a los productos activos
```

### Defaults de EmpresaModulo por selección

| Selección | `rubro_principal` | Módulos creados |
|---|---|---|
| Taller | `WORKSHOP` | `WORKSHOP` |
| Desarmaduría | `SALVAGE` | `SALVAGE` |
| Casa de repuestos | `PARTS` | `PARTS` |
| Más de uno | `MIXED` | `WORKSHOP` + `SALVAGE` + `PARTS` |

### Archivos involucrados

| Archivo | Cambio |
|---|---|
| `taller/forms/onboarding.py` | Agregar `tipo_producto` ChoiceField (no-modelo) |
| `templates/onboarding/paso_identidad.html` | Selector visual de producto (cards con íconos grandes) |
| `taller/views/onboarding_views.py` | `onboarding_guardar_paso` paso 1: escribir `rubro_principal` y crear filas en `EmpresaModulo` |
| `taller/services/company_defaults_service.py` | Método `provision_productos(empresa, tipo_producto)` |

---

## 6. Portal Público y SEO

### Estructura de URLs

```python
# En taller/urls_public.py o gestion_taller/urls.py

urlpatterns += [
    # Sin prefijo de país — raíces globales para SEO
    path("talleres/",      views.landing_workshop,    name="landing_workshop"),
    path("desarmadurias/", views.landing_salvage,     name="landing_salvage"),
    path("repuestos/",     views.landing_parts,       name="landing_parts"),

    # Con prefijo de país — SEO local
    path("cl/es/talleres/",          views.landing_workshop_cl),
    path("cl/es/desarmadurias/",     views.landing_salvage_cl),
    path("us/en/workshops/",         views.landing_workshop_us_en),
    path("us/en/salvage-yards/",     views.landing_salvage_us_en),
    path("us/es/deshuesaderos/",     views.landing_salvage_us_es),
    path("us/en/auto-parts/",        views.landing_parts_us_en),
]
```

### Templates de landing

```
templates/public/
├── base_landing.html                ← base compartida (nav mínimo, footer, SEO head)
├── landing_workshop.html            ← eGarage Workshop
├── landing_salvage.html             ← eGarage Salvage (incluye historia Atlanta)
├── landing_parts.html               ← eGarage Parts
└── landing_chile_completa.html      ← existente — no tocar hasta E6
```

### Historia Atlanta — obligatoria en `landing_salvage.html`

```html
<section class="historia-fundador" id="historia">
  <h2>Construido por alguien que conoce el negocio por dentro</h2>
  <p>
    Más de 20 años trabajando en talleres y desarmadurías en Atlanta, Georgia.
    Después de vivir el desorden del inventario, decidí crear el sistema
    que siempre necesité. eGarage Salvage es eso: el software que un
    operador de patio construiría para sí mismo.
  </p>
  <div class="caso-real">
    <strong>Atlanta Reciclajes SPA</strong> — el negocio donde eGarage
    Salvage se usa todos los días desde Chile.
  </div>
</section>
```

### Keywords SEO por producto e idioma

| Producto | Chile (CL/es) | USA-Latino (US/es) | USA-English (US/en) |
|---|---|---|---|
| Workshop | "software taller mecánico Chile" | "software taller mecánico USA" | "auto shop management software" |
| Salvage | "software desarmaduría Chile" | "software deshuesadero" / "software yonke" | "salvage yard software" / "junkyard inventory" |
| Parts | "software casa de repuestos Chile" | "software refaccionaria" | "auto parts store software" |

---

## 7. Producto Workshop — Estado y Especificación

### Estado actual: ~80% completo

No requiere construcción nueva. El flujo principal de talleres (cotización → OT → cierre → repuestos) funciona.

### Componentes exclusivos de Workshop

| Componente | Tabla | Archivo |
|---|---|---|
| Técnico/Mecánico | `taller_tecnico` | `models/tecnico.py` |
| Servicio | `taller_servicio` | `taller/servicios/` |
| Cita | `taller_cita` | `models/cita.py` |
| InspeccionIngreso | `taller_inspeccioningreso` | `models/inspeccion_ingreso.py` |
| Kilometraje | `taller_kilometraje` | `models/kilometraje.py` |

### Dashboard Workshop

Sección del dashboard habilitada si `empresa.tiene_producto("WORKSHOP")`:
- OTs abiertas / en proceso / cerradas
- Producción por técnico
- Repuestos más utilizados
- Tiempo promedio de reparación

---

## 8. Producto Salvage — Estado y Especificación

### Estado actual: ~75% completo

Los modelos, vistas y templates principales existen y funcionan. Lo que falta es el gate de autorización y la integración con `EmpresaModulo`.

### Modelos exclusivos de Salvage (ya existen)

| Modelo | Archivo actual |
|---|---|
| `VehiculoDesarme` | `taller/models/vehiculo_desarme.py` |
| `PiezaDesarme` | `taller/models/pieza_desarme.py` |
| `VentaDesarme` | `taller/models/venta_desarme.py` |
| `VendedorDesarme` | `taller/models/vendedor_desarme.py` |
| `InterchangePieza` | `taller/models/interchange_pieza.py` |
| `VehiculoFinancialSnapshot` | `taller/models/vehiculo_financial.py:10` |
| `VehicleFinancialEvent` | `taller/models/vehiculo_financial.py:64` |
| `CatalogoRepuestoEmpresa` | `taller/models/catalogo_repuesto_empresa.py` |

### Flujo operativo

```
1. Ingresar vehículo (VehiculoDesarme)
2. Registrar daños por zona
3. Crear piezas (PiezaDesarme) con código, precio, condición
4. Inventario disponible en lista + kiosco
5. Venta rápida → VentaDesarme → descuenta stock
6. Financiero: VehicleFinancialEvent por cada ingreso/egreso
7. Snapshot → ROI, recuperación %, health score
```

### Dashboard Salvage

Habilitado si `empresa.tiene_producto("SALVAGE")`:
- Piezas disponibles / vendidas / scrap
- Vehículos por estado
- ROI promedio del patio
- Top piezas vendidas
- Ingresos vs. inversión (timeline)

---

## 9. Producto Parts — Estado y Especificación

### Estado actual: ~15% completo

El modelo `Repuesto` existe pero fue diseñado para consumo en OTs. Se reutiliza; no se duplica.

### Modelos a construir

#### `Proveedor`
```python
class Proveedor(TenantScoped):
    nombre = models.CharField(max_length=200)
    rut_o_tax_id = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=40, blank=True)
    condicion_pago = models.CharField(
        max_length=20,
        choices=[("CONTADO","Contado"),("30_DIAS","30 días"),("60_DIAS","60 días")],
        default="CONTADO",
    )
    activo = models.BooleanField(default=True)

    class Meta(TenantScoped.Meta):
        verbose_name = "Proveedor"
```

#### `OrdenCompra` + `LineaOrdenCompra`
```python
class OrdenCompra(TenantScoped):
    numero = models.PositiveIntegerField()
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT)
    fecha = models.DateField(auto_now_add=True)
    estado = models.CharField(
        max_length=20,
        choices=[
            ("BORRADOR","Borrador"), ("ENVIADA","Enviada"),
            ("RECIBIDA_PARCIAL","Recibida parcialmente"),
            ("RECIBIDA_TOTAL","Recibida total"), ("ANULADA","Anulada"),
        ],
        default="BORRADOR",
    )

class LineaOrdenCompra(models.Model):
    orden = models.ForeignKey(OrdenCompra, on_delete=models.CASCADE, related_name="lineas")
    repuesto = models.ForeignKey("taller.Repuesto", on_delete=models.PROTECT)
    cantidad_pedida = models.PositiveIntegerField()
    cantidad_recibida = models.PositiveIntegerField(default=0)
    precio_costo = models.DecimalField(max_digits=12, decimal_places=2)
```

#### `MovimientoStock`
```python
class MovimientoStock(TenantScoped):
    repuesto = models.ForeignKey("taller.Repuesto", on_delete=models.PROTECT,
                                  related_name="movimientos")
    tipo = models.CharField(max_length=20, choices=[
        ("ENTRADA_COMPRA","Entrada por compra"),
        ("SALIDA_VENTA","Salida por venta directa"),
        ("SALIDA_OT","Salida por OT"),
        ("AJUSTE_POS","Ajuste positivo"),
        ("AJUSTE_NEG","Ajuste negativo"),
        ("DEVOLUCION","Devolución"),
    ])
    cantidad = models.IntegerField()          # positivo=entrada, negativo=salida
    stock_antes = models.IntegerField()
    stock_despues = models.IntegerField()
    referencia_id = models.IntegerField(null=True, blank=True)
    referencia_tipo = models.CharField(max_length=30, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey("auth.User", null=True, on_delete=models.SET_NULL)
```

### Relación con `Repuesto` existente

`MovimientoStock` traza los movimientos; el campo `cantidad_stock` en `Repuesto` es el saldo actual. Al recibir una `OrdenCompra`, el servicio crea un `MovimientoStock(tipo="ENTRADA_COMPRA")` y actualiza `repuesto.cantidad_stock`. Nunca se modifica `cantidad_stock` directamente.

### Dashboard Parts

Habilitado si `empresa.tiene_producto("PARTS")`:
- Valor total del inventario
- SKUs bajo stock mínimo
- Órdenes de compra pendientes de recibir
- Ventas directas del mes
- Margen bruto por categoría

---

## 10. Estrategia de Migración

### Tabla de migraciones planificadas

| ID | Nombre | Tipo | Riesgo | Backfill |
|---|---|---|---|---|
| M-01 | `create_empresa_modulo` | CREATE TABLE | Ninguno | Sí — `WORKSHOP + SALVAGE + PARTS` para todas las empresas existentes |
| M-02 | `add_salvage_to_rubro_choices` | ALTER FIELD choices | Ninguno | No |
| M-03 | `create_proveedor` | CREATE TABLE | Ninguno | No |
| M-04 | `create_orden_compra` | CREATE TABLE | Ninguno | No |
| M-05 | `create_movimiento_stock` | CREATE TABLE | Ninguno | No |
| M-06 | `backfill_modulos_por_rubro` | UPDATE | Bajo | Sí — ver detalle |

### Detalle M-06 — Backfill opcional post-lanzamiento

Solo se aplica **después** de que el onboarding lleve algunas semanas capturando la selección de producto, y solo para nuevas empresas. Las empresas existentes no se tocan.

```python
# M-06: quitar productos que no corresponden para empresas registradas después del lanzamiento de E1
# Solo para empresas cuyo onboarding fue completado después de la fecha de E1
def backfill_por_rubro(apps, schema_editor):
    ConfiguracionEmpresa = apps.get_model("taller", "ConfiguracionEmpresa")
    EmpresaModulo = apps.get_model("taller", "EmpresaModulo")
    for config in ConfiguracionEmpresa.objects.filter(
        empresa__onboarding_completed_at__gte=FECHA_LANZAMIENTO_E1
    ):
        if config.rubro_principal == "PARTS":
            EmpresaModulo.objects.filter(
                empresa=config.empresa,
                codigo__in=["WORKSHOP", "SALVAGE"]
            ).update(activo=False)
```

### Rollback por etapa

| Etapa | Rollback |
|---|---|
| E0 (landings) | Eliminar los 4 archivos nuevos + revertir `landing_inicio.html` |
| E1 (EmpresaModulo + onboarding) | `manage.py migrate taller M-00` + revertir forms/views/templates |
| E2 (auth backend) | Eliminar `taller/decorators.py` + quitar decorators de las vistas de desarme |
| E3 (MenuService + menú) | Eliminar `menu_service.py` + revertir `base.html` a versión anterior |
| E4 (onboarding especializado) | Revertir template + lógica de selección de template en `onboarding_views.py` |
| E5 (Parts completo) | Eliminar modelos + migraciones M-03/04/05 (sin datos en prod aún) |

---

## 11. Resumen de Decisiones Arquitectónicas

| Decisión | Elección | Alternativa descartada | Razón |
|---|---|---|---|
| ¿Modelo para módulos? | Tabla `EmpresaModulo` normalizada | Booleanos en ConfiguracionEmpresa | Extensible, auditable, sin crecer Config |
| ¿`rubro_principal` controla módulos? | No. Son dimensiones independientes | Derivar módulos del rubro siempre | Una empresa puede cambiar productos sin cambiar identidad |
| ¿Menú construido dónde? | `MenuService` en Python | Condicionales en `base.html` | Testeable, reutilizable, sin lógica en templates |
| ¿Qué va antes: auth o menú? | Auth backend (E2) antes que menú (E3) | Menú primero, auth después | Nunca ocultar algo sin protegerlo |
| ¿Nomenclatura interna? | `WORKSHOP / SALVAGE / PARTS` | `TALLER / DESARMADURIA / REPUESTOS` | Inglés canónico en código, español en UI |
| ¿Tabla EmpresaModulo ahora o después? | Ahora — es el diseño definitivo | Booleanos como paso intermedio | El paso intermedio crea deuda que hay que migrar |
| ¿Default para empresas existentes? | Backfill con los tres productos activos | `default=False` + backfill selectivo | No romper producción existente |
| ¿Dividir la app Django? | No. Sub-paquetes dentro de `taller/` | Nueva app Django por producto | Impacto en URLs, migrations, settings no justificado |
| ¿Historia de Atlanta en la landing? | Obligatoria en `landing_salvage.html` | Opcional o en sección separada | Es el único diferencial que no puede copiarse |
| ¿Casa de Repuestos en E1? | No. Solo modelos en E5+ | Todo de una vez | Validar demanda antes de construir |

---

*Ver ROADMAP_VERTICALS.md para el plan de implementación épica por épica.*
