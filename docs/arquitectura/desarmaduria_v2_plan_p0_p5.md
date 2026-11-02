# Desarmaduria v2 — Plan de Implementación P0–P5
**Fecha:** 2026-08-05  
**Estado:** P0, P1, P1.5 y P2-DB completos. P2 visual y P3–P5 pendientes.  
**Referencia:** `docs/arquitectura/desarmaduria_v2_propuesta.md`

---

## Estado de partida

| Fase | Estado |
|------|--------|
| P0 — Integridad de stock | **COMPLETO** (2026-08-05) |
| P1 — Campo `publicada` + filtros storefront | **COMPLETO** (2026-08-05) |
| P1.5 — Diseño Centro de Operaciones | **COMPLETO** (2026-08-05) |
| P2-DB — Base de datos del Centro de Operaciones | **COMPLETO** (2026-08-05) |
| P2 — Centro de Operaciones (visual) | Pendiente |
| P2.5 — "Así va tu negocio" (estadísticas) | Pendiente |
| P3 — Etapas físicas + publicación explícita | Pendiente |
| P4 — Reservas | Pendiente |
| P5 — Consolidación flujos + deprecación | Pendiente |

---

## P0 — Integridad de stock (COMPLETO)

**Objetivo:** Corregir el bug de stock sin introducir nuevas abstracciones.

### Cambios realizados

**`taller/desarme/views_inventario.py`**
- `select_for_update()` antes de decrementar stock en `finalizar_venta_desde_inventario`
- Validación de stock dentro de `transaction.atomic()` con excepción `_StockInsuficiente`
- `estado_pieza = VENDIDA` cuando `nueva_cantidad == 0`
- Corrección de `_redirect_to_documento_or_fallback` — añadido parámetro `request`

**`taller/views_extra/storefront.py`**
- `cantidad__gt=0` añadido al filtro base en `_tienda_storefront_render`
- `cantidad__gt=0` añadido al filtro base en `kiosko_centralizado`

**`taller/tests/test_venta_inventario_stock.py`** (nuevo)
- 10 tests cubren: venta total, parcial, sobre-venta, doble venta, storefront exclusión, multi-tenant, anulación

### No toca
- Esquema de modelos (no hay migraciones en P0)
- Templates
- URLs

---

## P1 — Campo `publicada` + filtros storefront

**Objetivo:** Introducir la compuerta del kiosko sin cambiar el flujo operativo visible.

**Prerequisito:** Decisión aprobada de continuar con v2.

### 1.1 Migración de modelos

**`taller/models/pieza_desarme.py`**
```python
publicada = models.BooleanField(default=False)
```

**Migración de datos (en la misma migration):**
```python
# Todos los PiezaDesarme activos con estado DISPONIBLE → publicada=True
# (retrocompatibilidad: piezas existentes siguen visibles)
PiezaDesarme.objects.filter(
    activo=True,
    estado_pieza=ESTADO_DISPONIBLE,
).update(publicada=True)
```

**Riesgo:** Registros existentes con `activo=True` pero `estado_pieza != DISPONIBLE` quedan con `publicada=False` — correcto, no deberían estar en kiosko.

### 1.2 Storefront

**`taller/views_extra/storefront.py`**
- Añadir `publicada=True` al filtro base en ambas funciones

**Orden de filtros final:**
```python
base_qs = PiezaDesarme.objects.filter(
    empresa=empresa,
    activo=True,
    publicada=True,          # v2
    estado_pieza=ESTADO_DISPONIBLE,
    cantidad__gt=0,          # P0
)
```

### 1.3 Tests

- `test_pieza_publicada_false_no_aparece_en_kiosko`
- `test_pieza_publicada_true_aparece_en_kiosko`
- `test_migracion_datos_piezas_existentes_quedan_publicadas`

### 1.4 Deploy check

Antes de deploy:
```sql
-- Verificar en producción cuántas piezas activas-disponibles hay
SELECT COUNT(*) FROM taller_piezadesarme WHERE activo=true AND estado_pieza='DISPONIBLE';
-- Todas deben quedar con publicada=true tras la migration
```

---

## P2 — Centro de Operaciones

**Objetivo:** Un hub único por vehículo que reemplaza `ver_vehiculo.html` como punto de entrada.

**Prerequisito:** P1 completo.

### 2.1 Campo `etapa` en VehiculoDesarme

**`taller/models/vehiculo_desarme.py`**
```python
ETAPA_INGRESADO      = "INGRESADO"
ETAPA_CONFIRMADO     = "CONFIRMADO"
ETAPA_EN_ALMACEN     = "EN_ALMACEN"
ETAPA_PUBLICADO      = "PUBLICADO"
ETAPA_VENDIENDO      = "VENDIENDO"
ETAPA_CERRADO        = "CERRADO"

ETAPAS_VEHICULO = [
    (ETAPA_INGRESADO,  "Ingresado"),
    (ETAPA_CONFIRMADO, "Confirmado"),
    (ETAPA_EN_ALMACEN, "En almacén"),
    (ETAPA_PUBLICADO,  "Publicado"),
    (ETAPA_VENDIENDO,  "Vendiendo"),
    (ETAPA_CERRADO,    "Cerrado"),
]

etapa = models.CharField(
    max_length=20,
    choices=ETAPAS_VEHICULO,
    default=ETAPA_INGRESADO,
)
```

**Migración de datos:**
```python
# Vehículos existentes → inferir etapa desde datos actuales
# Si tiene PiezaDesarme publicadas → PUBLICADO
# Si tiene PiezaDesarme confirmadas → CONFIRMADO
# Default → INGRESADO
```

### 2.2 View centro_operaciones

**`taller/desarme/views.py`** — nueva view:
```python
@login_required
def centro_operaciones(request, pais, lang, pk):
    empresa = get_empresa(request)
    vehiculo = get_object_or_404(VehiculoDesarme, pk=pk, empresa=empresa)
    
    context = {
        "vehiculo": vehiculo,
        "kpis": _calcular_kpis_vehiculo(vehiculo),
        "acciones_disponibles": _acciones_por_etapa(vehiculo.etapa),
    }
    return render(request, "taller/desarme/centro_operaciones.html", context)
```

### 2.3 Template centro_operaciones.html

Estructura del template:
```
[ Panel de estado: etapa actual + progreso visual ]
[ KPIs: N confirmadas | N publicadas | N vendidas | $ ingresos ]
[ Acciones contextuales por etapa ]
[ Historial de acciones del vehículo ]
```

### 2.4 URL

```python
path("vehiculos/<int:pk>/centro/", views.centro_operaciones, name="centro_operaciones"),
```

### 2.5 Redirect de crear_vehiculo

```python
# views.py::crear_vehiculo — después de inicializar_sugerencias()
return redirect(_desarme_url(request, f"vehiculos/{vehiculo.pk}/centro/"))
```

### 2.6 Tests

- `test_centro_operaciones_requiere_auth`
- `test_centro_operaciones_muestra_etapa`
- `test_centro_operaciones_aislamiento_tenant`
- `test_acciones_contextuales_por_etapa` (parametrizado)

---

## P2.5 — "Así va tu negocio" — Estadísticas y Rentabilidad

**Objetivo:** Convertir los datos del flujo operativo en información accionable para el operador, en lenguaje de negocio. Nombre visible: **"Así va tu negocio"**.

**Prerequisito:** P2 completo (campo `etapa` en `VehiculoDesarme` disponible).

**Referencia completa:** `docs/arquitectura/desarmaduria_v2_estadisticas_negocio.md` y `desarmaduria_v2_experiencia_humana.md`.

### 2.5.1 Nuevo archivo: `views_stats.py`

```python
# taller/desarme/views_stats.py

def kpis_vehiculo(vehiculo) -> dict:
    """Calcula los KPIs de un vehículo para el Centro de Operaciones."""
    # Ingresos canónicos (Documento + LineaRepuesto)
    # Ingresos legados (VentaDesarme + LineaVentaDesarme)
    # Valor potencial restante (piezas con precio > 0)
    # Conteos de piezas por estado
    # Alertas activas
    # Ver fórmulas completas en desarmaduria_v2_estadisticas_negocio.md §8.1

def kpis_empresa(empresa, periodo="mes") -> dict:
    """Calcula los KPIs agregados para el dashboard empresa."""
    # Inventario activo total
    # Ingresos del período
    # ROI promedio vehículos cerrados
    # Vehículos en radar de atención
    # Top piezas vendidas

@login_required
def dashboard_estadisticas(request, pais, lang):
    empresa = get_empresa(request)
    periodo = request.GET.get("periodo", "mes")
    context = {
        "kpis": kpis_empresa(empresa, periodo),
        "vehiculos": VehiculoDesarme.objects.filter(
            empresa=empresa,
            estado_desarme__ne="CERRADO",
        ).select_related().prefetch_related("piezadesarme_set"),
    }
    return render(request, "taller/desarme/dashboard_asi_va_tu_negocio.html", context)
```

### 2.5.2 Template: `dashboard_asi_va_tu_negocio.html`

Estructura de tres niveles (ver `desarmaduria_v2_experiencia_humana.md` §5.1):

- **Nivel 1** (header): 4 KPIs grandes — Inventario activo / Ingresos del mes / ROI promedio / Por recuperar
- **Nivel 2** (alertas): bloque "Requiere atención" con alertas accionables
- **Nivel 3** (lista): tabla de vehículos con barra de progreso de recuperación

### 2.5.3 Partial: `partials/_kpis_vehiculo.html`

Incluido desde `centro_operaciones.html`:
```html
{% include "taller/desarme/partials/_kpis_vehiculo.html" with kpis=kpis %}
```

Muestra:
- Costo / Generado / % recuperado / Falta recuperar (fila de 4 números)
- Barra de piezas: VENDIDAS | DISPONIBLES | RESERVADAS | SIN PUBLICAR
- Potencial si vendes todo + proyección total
- Alertas del vehículo (piezas sin precio, sin costo, reservas vencidas)

### 2.5.4 URL

```python
path("estadisticas/", views_stats.dashboard_estadisticas, name="estadisticas"),
```

### 2.5.5 Integración con Centro de Operaciones

```python
# views.py::centro_operaciones — añadir kpis al contexto
from taller.desarme.views_stats import kpis_vehiculo

def centro_operaciones(request, pais, lang, pk):
    ...
    context = {
        "vehiculo": vehiculo,
        "kpis": kpis_vehiculo(vehiculo),   # nuevo
        "acciones_disponibles": _acciones_por_etapa(vehiculo.etapa),
    }
```

### 2.5.6 Calidad de datos — manejo de datos faltantes

El sistema no bloquea ni rompe cuando faltan datos. Reglas:
- `costo_adquisicion = NULL` → mostrar "Registra el costo para ver tu rentabilidad" + botón inline
- `precio_venta_sugerido = 0` → excluir del potencial + alerta "N piezas sin precio"
- `ingresos_totales = 0` → mostrar "Sin ventas aún. Ingresado hace N días."
- División por cero (ROI sin costo) → mostrar `None`, no calcular

### 2.5.7 Tests

- `test_kpis_vehiculo_sin_ventas` — KPIs correctos cuando no hay ventas
- `test_kpis_vehiculo_con_ventas_canonicas` — suma correcta de LineaRepuesto
- `test_kpis_vehiculo_con_ventas_legadas` — suma correcta de LineaVentaDesarme
- `test_kpis_vehiculo_ambos_flujos` — suma correcta combinada
- `test_kpis_vehiculo_sin_costo` — no rompe, retorna `costo_registrado=False`
- `test_kpis_vehiculo_piezas_sin_precio` — excluye del potencial, cuenta en `sin_precio`
- `test_kpis_empresa_inventario_activo` — suma correcta de valor disponible
- `test_dashboard_estadisticas_requiere_auth` — 302 si no autenticado
- `test_dashboard_estadisticas_aislamiento_tenant` — no cruza datos de otra empresa

### 2.5.8 Criterios de aceptación

Un operador sin formación contable debe responder estas preguntas en < 10 segundos:

- ¿Cuánto pagué por este auto?
- ¿Cuánto he generado con él?
- ¿Recuperé la inversión?
- ¿Tengo algo urgente que atender?

Si un KPI requiere explicación verbal, rediseñar antes de implementar.

---

## P3 — Etapas físicas + publicación explícita

**Objetivo:** Desacoplar "pieza confirmada" de "pieza visible en kiosko". Operador decide cuándo publicar.

**Prerequisito:** P2.5 completo.

### 3.1 Campo `etapa_fisica` en PiezaDesarme

```python
ETAPA_FISICA_CONFIRMADA  = "CONFIRMADA"
ETAPA_FISICA_DESMONTADA  = "DESMONTADA"
ETAPA_FISICA_ALMACENADA  = "ALMACENADA"

etapa_fisica = models.CharField(
    max_length=20,
    choices=[...],
    default=ETAPA_FISICA_CONFIRMADA,
)
```

### 3.2 Revisar_vehiculo — botón "Finalizar revisión"

**`revisar_vehiculo`:** Añadir acción `finalizar` que:
1. Verifica que no queden sugerencias en PENDIENTE (o las descarta automáticamente)
2. `vehiculo.etapa = ETAPA_CONFIRMADO`
3. Redirect a `centro_operaciones`

### 3.3 Scanner_vehiculo — nuevo rol

Rol actual: asignar precios y condición.  
Rol v2: tracker de desmonte físico.

Añadir a la view:
```python
# Marcar pieza como desmontada
pieza.etapa_fisica = ETAPA_FISICA_DESMONTADA
pieza.ubicacion_fisica = request.POST.get("ubicacion")
pieza.save(update_fields=["etapa_fisica", "ubicacion_fisica"])

# Si todas las piezas del vehículo están DESMONTADAS o ALMACENADAS:
if not vehiculo.piezas.filter(etapa_fisica=ETAPA_FISICA_CONFIRMADA).exists():
    vehiculo.etapa = ETAPA_EN_ALMACEN
    vehiculo.save(update_fields=["etapa"])
```

### 3.4 View publicar_piezas (nueva)

```python
@login_required
def publicar_piezas(request, pais, lang, pk):
    empresa = get_empresa(request)
    vehiculo = get_object_or_404(VehiculoDesarme, pk=pk, empresa=empresa)
    
    if request.method == "POST":
        pieza_ids = request.POST.getlist("pieza_ids")
        # Solo se pueden publicar piezas que ya estén DESMONTADA o ALMACENADA (invariante físico)
        # publicar_piezas NO modifica etapa_fisica — la transición física es responsabilidad exclusiva de scanner_vehiculo
        PiezaDesarme.objects.filter(
            pk__in=pieza_ids,
            vehiculo_desarme=vehiculo,
            empresa=empresa,
            publicada=False,
            etapa_fisica__in=[ETAPA_FISICA_DESMONTADA, ETAPA_FISICA_ALMACENADA],
        ).update(publicada=True)
        
        if vehiculo.piezas.filter(publicada=False, activo=True).exists():
            vehiculo.etapa = ETAPA_EN_ALMACEN
        else:
            vehiculo.etapa = ETAPA_PUBLICADO
        vehiculo.save(update_fields=["etapa"])
        
        return redirect(_desarme_url(request, f"vehiculos/{vehiculo.pk}/centro/"))
    
    piezas = vehiculo.piezas.filter(publicada=False, activo=True)
    return render(request, "taller/desarme/publicar_piezas.html", {"vehiculo": vehiculo, "piezas": piezas})
```

### 3.5 Tests

- `test_confirmar_pieza_crea_publicada_false`
- `test_publicar_pieza_cambia_publicada_true`
- `test_finalizar_revision_avanza_etapa_a_confirmado`
- `test_publicar_todas_avanza_etapa_a_publicado`

---

## P4 — Reservas

**Objetivo:** Permitir que un comprador reserve una pieza antes de comprarla.

**Prerequisito:** P3 completo.

### 4.1 Nuevo modelo `ReservaDesarme`

```python
class ReservaDesarme(TenantScoped):
    pieza = models.ForeignKey(PiezaDesarme, on_delete=models.CASCADE)
    nombre_comprador = models.CharField(max_length=200)
    telefono = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    fecha_expiracion = models.DateTimeField()
    activa = models.BooleanField(default=True)
    
    class Meta:
        indexes = [models.Index(fields=["pieza", "activa"])]
```

### 4.2 Flujo de reserva

```
Kiosko / Panel interno
    → POST reservar_pieza
        → pieza.estado_pieza = RESERVADA
        → ReservaDesarme.create(expira en X horas)
        → Notificación WhatsApp al operador (opcional)

Tarea periódica (cron / management command)
    → ReservaDesarme vencidas → pieza.estado_pieza = DISPONIBLE

Panel interno
    → Liberar reserva → DISPONIBLE
    → Confirmar reserva → flujo canónico de venta
```

### 4.3 Configuración de tiempo de reserva

```python
# En Empresa o ConfiguracionDesarme:
horas_reserva = models.PositiveIntegerField(default=48)
```

---

## P5 — Consolidación flujos + deprecación

**Objetivo:** Eliminar flujos paralelos y templates huérfanos. Completar la migración al flujo canónico.

**Prerequisito:** P4 completo. Al menos 30 días de uso de v2 en producción.

### 5.1 Deprecar `inventario_vehiculo.html`

1. Añadir redirect en la view que sirve `inventario_vehiculo.html` → `inventario_inteligente.html`
2. Medir tráfico real durante 2 semanas
3. Si tráfico = 0, eliminar template y view

### 5.2 Congelar `VentaDesarme` en modo mantenimiento

- UI de `iniciar_venta_rapida` muestra banner: "Este flujo está en mantenimiento. Usar inventario inteligente."
- No eliminar: los datos históricos de `VentaDesarme` son válidos para reportes

### 5.3 Eliminar huérfanos

```
templates/taller/desarme/dashboard_financiero.html  → eliminar
templates/taller/desarme/partials/_inventario_sale_panel.html  → eliminar
```

Verificar antes:
```bash
grep -r "dashboard_financiero" templates/ taller/ --include="*.html" --include="*.py"
grep -r "_inventario_sale_panel" templates/ taller/ --include="*.html" --include="*.py"
```

### 5.4 Eliminar BAK files

```
taller/desarme/views_inventario.py.bak
taller/desarme/views.py.bak
# ... otros 6 .bak files identificados en auditoría
```

### 5.5 Tests de regresión post-P5

- Verificar que todos los tests de P0 siguen pasando
- Test de humo de kiosko: pieza visible después de publicar
- Test de humo de venta: `finalizar_venta_desde_inventario` exitoso de extremo a extremo

---

## Resumen de cambios por capa

| Capa | P0 | P1 | P2 | P2.5 | P3 | P4 | P5 |
|------|----|----|----|----|----|----|-----|
| **Modelos** | — | `publicada` en PiezaDesarme | `etapa` en VehiculoDesarme | — | `etapa_fisica` en PiezaDesarme | `ReservaDesarme` (nuevo) | — |
| **Migraciones** | — | 1 + data migration | 1 + data migration | — | 1 | 1 | — |
| **Views** | `views_inventario.py` | `storefront.py` | `centro_operaciones` (nueva) | `views_stats.py` (nuevo) | `publicar_piezas`, `revisar` + `scanner` | `reservar_pieza` (nueva) | limpiar |
| **Templates** | — | — | `centro_operaciones.html` (nuevo) | `dashboard_asi_va_tu_negocio.html`, `_kpis_vehiculo.html` | `publicar_piezas.html` (nuevo) | template reserva | eliminar huérfanos |
| **URLs** | — | — | `vehiculos/<pk>/centro/` | `estadisticas/` | `vehiculos/<pk>/publicar/` | `piezas/<pk>/reservar/` | limpiar |
| **Tests** | 10 tests | 3 tests | 4 tests | 9 tests | 4 tests | 3 tests | regresión |

---

## Criterios de aprobación antes de iniciar cada fase

| Fase | Criterio de entrada | Criterio de salida |
|------|--------------------|--------------------|
| P1 | Decisión arquitectural aprobada | Migración validada contra clon prod |
| P2 | P1 en prod sin incidentes 7 días | `centro_operaciones` probado con 5 vehículos reales |
| P2.5 | P2 en prod estable | Operador responde "¿cuánto gané con este auto?" en < 10 seg sin asistencia |
| P3 | P2.5 en prod sin incidentes 7 días | Operador completa flujo publicar end-to-end sin asistencia |
| P4 | P3 en prod sin incidentes 14 días | Primera reserva exitosa en prod |
| P5 | P4 en prod sin incidentes 30 días | Tráfico cero a URLs deprecadas |
