# Desarmaduria v2 — Módulo "Así va tu negocio"
**Fecha:** 2026-08-05  
**Estado:** Diseño técnico. Sin implementación aprobada.  
**Referencia:** `docs/arquitectura/desarmaduria_v2_propuesta.md`, `desarmaduria_v2_experiencia_humana.md`

---

## 1. Principio rector

> Las estadísticas no son gráficos decorativos.  
> Deben responder seis preguntas en lenguaje de negocio:  
> **¿cuánto entró? ¿cuánto salió? ¿cuánto gané? ¿cuánto falta recuperar? ¿qué requiere atención? ¿qué conviene hacer ahora?**

El nombre visible del módulo es **"Así va tu negocio"**.

Un operador de desarmaduria no es un analista de datos. No sabe qué es un EBITDA. Sí sabe si compró un Hilux en $3.000.000 y quiere saber si va a recuperar lo que pagó. Las métricas deben responder esa pregunta directamente.

---

## 2. Alcance del módulo

El módulo opera en **dos niveles de agregación**:

| Nivel | Vista | Pregunta central |
|-------|-------|-----------------|
| **Por vehículo** | Centro de Operaciones (panel lateral o tab) | ¿Este auto está siendo rentable? |
| **Por empresa** | Dashboard "Así va tu negocio" | ¿Mi negocio de desarmaduria va bien? |

Ambos niveles comparten las mismas fórmulas; solo difiere el scope del queryset.

---

## 3. KPIs — definiciones y fórmulas

### 3.1 KPIs por vehículo

#### A. Costo de adquisición
```
costo = VehiculoDesarme.costo_adquisicion
```
**Calidad:** Si `costo_adquisicion` es null o 0, el KPI muestra "Sin costo registrado" y los cálculos de ROI se marcan como incompletos.

---

#### B. Ingresos totales generados
```
ingresos_canonicos = SUM(
    LineaRepuesto.subtotal
    WHERE LineaRepuesto.documento.empresa = empresa
      AND LineaRepuesto.pieza.vehiculo_desarme = vehiculo
      AND LineaRepuesto.origen_repuesto = ORIGEN_DESARME
      AND LineaRepuesto.documento.estado NOT IN ('ANULADO', 'BORRADOR')
      AND LineaRepuesto.documento.fecha_emision IS NOT NULL
)

ingresos_rapidos = SUM(
    LineaVentaDesarme.cantidad * LineaVentaDesarme.precio_unitario
    WHERE LineaVentaDesarme.venta.empresa = empresa
      AND LineaVentaDesarme.pieza.vehiculo_desarme = vehiculo
      AND LineaVentaDesarme.venta.anulada = False
)

ingresos_totales = ingresos_canonicos + ingresos_rapidos
```
**Fuente:** `Documento + LineaRepuesto` (flujo canónico) + `VentaDesarme + LineaVentaDesarme` (flujo legado).  
**Calidad:** Si hay ventas en ambos sistemas para el mismo vehículo, se suman. No hay duplicación porque los stocks son independientes por flujo.

---

#### C. % recuperado del costo
```
pct_recuperado = (ingresos_totales / costo) * 100
```
**Presentación:** "Recuperaste el 87% de lo que pagaste."  
**Umbral visual:**
- < 50%: indicador rojo — "Atención, vas por debajo de la mitad"
- 50%–99%: indicador amarillo — "Vas bien, falta recuperar X"
- ≥ 100%: indicador verde — "Recuperaste el costo. Lo que sigue es ganancia"
- > 120%: indicador destacado — "Muy buen resultado"

**Calidad:** Si `costo = 0` o null → no calcular, mostrar "Registra el costo de compra para ver este dato".

---

#### D. Ganancia bruta
```
ganancia_bruta = ingresos_totales - costo
```
**Presentación:** Positivo = ganancia. Negativo = pérdida ("Todavía no recuperas la inversión").  
**No incluye:** costos operativos, mano de obra, overhead. Solo costo de adquisición vs ventas.

---

#### E. Valor potencial restante
```
valor_potencial_restante = SUM(
    PiezaDesarme.precio_venta_sugerido * PiezaDesarme.cantidad
    WHERE vehiculo_desarme = vehiculo
      AND estado_pieza IN (DISPONIBLE, RESERVADA)
      AND activo = True
)
```
**Presentación:** "Si vendieras todo lo que queda publicado: $X"  
**Calidad:** Si alguna pieza tiene `precio_venta_sugerido = 0` o null, excluirla del cálculo y mostrar alerta: "N piezas sin precio — regístralos para ver el potencial completo."

**Proyección combinada:**
```
potencial_total = ingresos_totales + valor_potencial_restante
```
"Si vendes todo lo que tienes, habrás generado $X en total."

---

#### F. Piezas — resumen visual
```
total_confirmadas  = COUNT(PiezaDesarme WHERE vehiculo = v AND activo = True)
publicadas         = COUNT(... AND publicada = True)
vendidas           = COUNT(... AND estado_pieza = VENDIDA)
disponibles        = COUNT(... AND publicada = True AND estado_pieza = DISPONIBLE AND cantidad > 0)
reservadas         = COUNT(... AND estado_pieza = RESERVADA)
descartadas        = COUNT(SugerenciaPiezaDesarme WHERE vehiculo = v AND estado = DESCARTADA)
sin_precio         = COUNT(... AND precio_venta_sugerido IS NULL OR precio_venta_sugerido = 0)
```
**Presentación:** Mini barra horizontal con segmentos coloreados.
```
[  VENDIDAS ████  |  DISPONIBLES ████  |  RESERVADAS ██  |  SIN PUBLICAR ██  ]
```

---

#### G. Velocidad de venta
```
dias_hasta_primera_venta = (fecha_primera_venta - fecha_ingreso_vehiculo).days
```
Donde `fecha_primera_venta` = fecha del Documento o VentaDesarme más temprano relacionado al vehículo.

**Presentación:** "Primera venta: 3 días después del ingreso."  
**Calidad:** Si no hay ventas → "Sin ventas aún. Ingresado hace N días."

---

#### H. Alertas por vehículo
```
alerta_sin_costo          = (costo_adquisicion IS NULL OR costo = 0)
alerta_piezas_sin_precio  = (sin_precio > 0)
alerta_reservas_vencidas  = (ReservaDesarme.activa = True AND fecha_expiracion < now())
alerta_estancado          = (etapa = PUBLICADO AND dias_publicado > 30 AND vendidas = 0)
alerta_sin_publicar       = (etapa IN (CONFIRMADO, EN_ALMACEN) AND dias_en_etapa > 7)
```

---

### 3.2 KPIs por empresa (dashboard agregado)

#### A. Inventario activo total
```
valor_inventario_activo = SUM(
    precio_venta_sugerido * cantidad
    WHERE empresa = e
      AND publicada = True
      AND estado_pieza = DISPONIBLE
      AND activo = True
)
```
**Presentación:** "Tienes $X en piezas disponibles para vender."

---

#### B. Ingresos por período
```
ingresos_mes_actual = ingresos donde:
    Documento.fecha_emision >= inicio_mes_actual  (flujo canónico)
    VentaDesarme.created_at >= inicio_mes_actual  (flujo legado)

ingresos_mes_anterior = ídem con rango de mes anterior

variacion_pct = ((ingresos_mes_actual - ingresos_mes_anterior) / ingresos_mes_anterior) * 100
    → Si ingresos_mes_anterior = 0: no calcular variación (división por cero → mostrar "Sin comparativa")
```
**Campo de fecha canónico:** `Documento.fecha_emision` (no `created_at`).  
**Campo de fecha legado:** `VentaDesarme.created_at` (no tiene `fecha_emision`).  
**Períodos disponibles:** Semana actual, mes actual, mes anterior, año en curso.

---

#### C. ROI promedio por vehículo cerrado
```
roi_promedio = AVG(
    (ingresos_vehiculo - costo_vehiculo) / costo_vehiculo * 100
    WHERE vehiculo.estado_desarme = CERRADO
      AND costo_vehiculo > 0
)
```
**Filtro:** Solo vehículos cerrados, con costo registrado.

---

#### D. Vehículos en radar de atención
```
vehiculos_sin_actividad = VehiculoDesarme WHERE (
    etapa = PUBLICADO
    AND dias_en_etapa > 30
    AND COUNT(ventas) = 0
)
vehiculos_estancados = WHERE (
    etapa IN (INGRESADO, CONFIRMADO, EN_ALMACEN)
    AND dias_en_etapa > 14
)
piezas_sin_precio = COUNT(PiezaDesarme WHERE precio = 0 AND activo = True)
```

---

#### E. Ranking de piezas más vendidas
```
top_piezas = LineaRepuesto + LineaVentaDesarme
    GROUP BY nombre_normalizado(pieza.nombre)
    ORDER BY COUNT(*) DESC
    LIMIT 10
```
**Uso:** Ayuda al operador a priorizar qué piezas publicar y a qué precio.

---

#### F. Marca/modelo más rentable
```
roi_por_marca_modelo = (
    SELECT marca, modelo, AVG(roi_vehiculo)
    FROM vehiculos_con_costo_y_ventas
    WHERE cerrado = True
    GROUP BY marca, modelo
    ORDER BY AVG(roi_vehiculo) DESC
)
```

---

## 4. Fuentes de datos

| KPI | Modelo | Campo | Notas |
|-----|--------|-------|-------|
| Costo adquisición | `VehiculoDesarme` | `costo_adquisicion` | Puede ser null |
| Ingresos canónicos | `LineaRepuesto` | `subtotal` | `origen_repuesto=ORIGEN_DESARME` |
| Ingresos legado | `LineaVentaDesarme` | `cantidad * precio_unitario` | `venta.anulada=False` |
| Precio pieza | `PiezaDesarme` | `precio_venta_sugerido` | Puede ser 0/null |
| Stock disponible | `PiezaDesarme` | `cantidad` | `estado=DISPONIBLE, activo=True` |
| Fecha primera venta | `Documento` / `VentaDesarme` | `fecha_emision` / `created_at` | MIN() por vehículo |
| Fecha ingreso vehículo | `VehiculoDesarme` | `created_at` | No tiene campo `fecha_ingreso` separado |
| Etapa actual | `VehiculoDesarme` | `etapa` | Campo nuevo v2 (P2) |
| Reservas | `ReservaDesarme` | `activa`, `fecha_expiracion` | Modelo nuevo (P4) |

---

## 5. Calidad de datos — casos problemáticos

### 5.1 Costo de adquisición faltante
**Frecuencia:** Alta. Los vehículos ingresados antes de v2 no tienen este campo obligatorio.  
**Efecto:** Los KPIs de ROI, % recuperado y ganancia bruta no se pueden calcular.  
**Respuesta del sistema:**
- Mostrar el resto de KPIs normalmente
- En lugar de ROI: "Agrega el costo de compra para ver tu rentabilidad"
- Botón inline: "Registrar costo ahora"

### 5.2 Piezas sin precio
**Frecuencia:** Media. Piezas confirmadas pero aún sin precio asignado.  
**Efecto:** `valor_potencial_restante` subestimado.  
**Respuesta del sistema:**
- Calcular con las que tienen precio
- Mostrar: "N piezas sin precio no están incluidas en este total"
- Alerta accionable: link a la lista de piezas sin precio

### 5.3 Ventas en ambos flujos para el mismo vehículo
**Frecuencia:** Media. Operadores que usaban venta rápida y luego migraron al flujo canónico.  
**Efecto:** Necesario sumar ambos flujos para no subestimar ingresos.  
**Decisión de diseño:** Sumar siempre. Nunca elegir uno u otro.

### 5.4 Documento anulado o en borrador
**Efecto:** Si un Documento está anulado o en borrador, sus LineaRepuesto no cuentan como ingreso.  
**Query:** Siempre filtrar `documento.estado NOT IN ('ANULADO', 'BORRADOR')`.  
**Motivo:** Un BORRADOR no es una venta realizada. Solo documentos emitidos (`fecha_emision IS NOT NULL`) representan ingresos reales.

### 5.5 VentaDesarme anulada
**Efecto:** Si una VentaDesarme está anulada, no cuenta como ingreso.  
**Query:** Filtrar `venta.anulada = False`.

### 5.6 PiezaDesarme con `activo=False`
**Decisión:** Excluir del valor potencial. Una pieza inactivada fue retirada del sistema.  
**Incluir en historial:** Sí, para el conteo de "piezas descartadas operacionalmente".

---

## 6. Diseño de la experiencia — "Así va tu negocio"

### 6.1 Estructura visual del dashboard empresa

```
┌─────────────────────────────────────────────────────────────┐
│  Así va tu negocio              [Semana | Mes | Año]        │
├──────────────┬──────────────┬──────────────┬────────────────┤
│  $X,XXX,XXX  │  $X,XXX,XXX  │    XX%       │   $X,XXX,XXX   │
│  Inventario  │  Ingresos    │  ROI prom.   │  Por recuperar │
│  disponible  │  este mes    │  vehículos   │  (publicado)   │
├──────────────┴──────────────┴──────────────┴────────────────┤
│  REQUIERE ATENCIÓN                                          │
│  ⚠ 2 vehículos publicados hace +30 días sin ventas → [Ver] │
│  ⚠ 14 piezas sin precio registrado → [Completar]           │
│  ⚠ 1 reserva vencida sin resolver → [Revisar]              │
├─────────────────────────────────────────────────────────────┤
│  MIS VEHÍCULOS    [Todos | Activos | Cerrados]              │
│                                                             │
│  Hilux 2018   ████████░░  87% recuperado   $245.000 queda  │
│  Corolla 2019 ██████████  104% — ganancia  Cerrado ✓        │
│  Focus 2020   ████░░░░░░  42% recuperado   [Atencion]      │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Panel de vehículo en Centro de Operaciones

```
┌─────────────────────────────────────────────────────────────┐
│  Toyota Hilux 2018 — Patente XXXX                           │
│  Ingresado hace 12 días  ·  Etapa: VENDIENDO                │
├──────────────┬──────────────┬──────────────┬────────────────┤
│  $3.000.000  │  $2.610.000  │    87%       │  $390.000 más  │
│  Costo       │  Generado    │  Recuperado  │  para cubrir   │
├──────────────┴──────────────┴──────────────┴────────────────┤
│  Piezas  [████VENDIDAS 8████|████DISPONIBLE 12████|RESERV 2]│
│          de 25 confirmadas · 3 sin precio · 0 sin publicar  │
├─────────────────────────────────────────────────────────────┤
│  Potencial restante si vendes todo: $1.240.000              │
│  → Total proyectado: $3.850.000 (28% de ganancia)           │
└─────────────────────────────────────────────────────────────┘
```

### 6.3 Lenguaje

| No decir | Decir en cambio |
|----------|----------------|
| "ROI: 87%" | "Recuperaste el 87% de lo que pagaste" |
| "Ingresos: $2.610.000" | "Generaste $2.610.000 con este vehículo" |
| "Valor inventario: $1.240.000" | "Si vendieras todo lo que tienes publicado: $1.240.000" |
| "Delta MoM: +12%" | "Este mes generaste 12% más que el mes pasado" |
| "N/A" | "Registra el costo de compra para ver este dato" |
| "0 ventas (30 días)" | "Este auto lleva 30 días publicado sin ventas — ¿bajamos el precio?" |

---

## 7. Datos de entrada requeridos del operador

Para que los KPIs funcionen con calidad completa, el operador debe registrar:

| Campo | Dónde | Obligatorio para |
|-------|-------|-----------------|
| `costo_adquisicion` | `vehiculo_form.html` | ROI, % recuperado, ganancia |
| `precio_venta_sugerido` por pieza | `revisar_vehiculo.html` o `scanner_vehiculo.html` | Valor potencial restante |
| Fecha de venta (automático) | `finalizar_venta_desde_inventario` | Velocidad de venta |

Si el operador no registra el costo al crear el vehículo, el sistema debe ofrecer registrarlo desde el Centro de Operaciones sin tener que editar el formulario completo.

---

## 8. Queries de referencia

### 8.1 KPIs rápidos de un vehículo
```python
from django.db.models import Sum, Count, F, Q
from decimal import Decimal

def kpis_vehiculo(vehiculo):
    empresa = vehiculo.empresa

    # Ingresos flujo canónico (excluir ANULADO y BORRADOR; usar fecha_emision para filtros de período)
    ingresos_doc = LineaRepuesto.objects.filter(
        pieza__vehiculo_desarme=vehiculo,
        origen_repuesto=ORIGEN_DESARME,
        documento__fecha_emision__isnull=False,
    ).exclude(
        documento__estado__in=["ANULADO", "BORRADOR"],
    ).aggregate(total=Sum("subtotal"))["total"] or Decimal("0")

    # Ingresos flujo legado
    ingresos_vd = LineaVentaDesarme.objects.filter(
        pieza__vehiculo_desarme=vehiculo,
        venta__anulada=False,
    ).aggregate(total=Sum(F("cantidad") * F("precio_unitario")))["total"] or Decimal("0")

    ingresos_totales = ingresos_doc + ingresos_vd

    # IMPORTANTE: costo NULL ≠ costo 0. Si no hay costo registrado, los KPIs dependientes retornan None.
    costo_raw = vehiculo.costo_adquisicion  # puede ser None
    costo_registrado = bool(costo_raw and costo_raw > 0)

    # Valor potencial
    valor_potencial = PiezaDesarme.objects.filter(
        vehiculo_desarme=vehiculo,
        activo=True,
        estado_pieza__in=[ESTADO_DISPONIBLE, ESTADO_RESERVADA],
        precio_venta_sugerido__gt=0,
    ).aggregate(
        total=Sum(F("precio_venta_sugerido") * F("cantidad"))
    )["total"] or Decimal("0")

    # Conteos de piezas
    piezas_qs = PiezaDesarme.objects.filter(vehiculo_desarme=vehiculo, activo=True)
    conteos = piezas_qs.aggregate(
        total=Count("pk"),
        publicadas=Count("pk", filter=Q(publicada=True)),
        vendidas=Count("pk", filter=Q(estado_pieza=ESTADO_VENDIDA)),
        disponibles=Count("pk", filter=Q(
            publicada=True, estado_pieza=ESTADO_DISPONIBLE, cantidad__gt=0
        )),
        sin_precio=Count("pk", filter=Q(precio_venta_sugerido__isnull=True) | Q(precio_venta_sugerido=0)),
    )

    return {
        "costo": costo_raw,  # None si no registrado
        "ingresos_totales": ingresos_totales,
        "ganancia_bruta": (ingresos_totales - costo_raw) if costo_registrado else None,  # None ≠ 0
        "pct_recuperado": (ingresos_totales / costo_raw * 100) if costo_registrado else None,
        "valor_potencial_restante": valor_potencial,
        "potencial_total": ingresos_totales + valor_potencial,
        "conteos": conteos,
        "costo_registrado": costo_registrado,
    }
```

---

## 9. Criterios de aceptación humana

Un operador sin formación contable debe poder responder estas preguntas en menos de 10 segundos mirando el dashboard:

| Pregunta | KPI que la responde | Tiempo objetivo |
|----------|--------------------|-----------------||
| ¿Cuánto pagué por este auto? | Costo de adquisición | < 2 seg |
| ¿Cuánto he ganado con él hasta hoy? | Ingresos totales generados | < 2 seg |
| ¿Recuperé lo que invertí? | % recuperado + color semáforo | < 2 seg |
| ¿Cuánto me falta recuperar? | Costo − Ingresos (si negativo) | < 2 seg |
| ¿Tengo algo urgente que atender? | Bloque "Requiere atención" | < 5 seg |
| ¿Cuál es mi mejor marca para comprar? | Ranking ROI por marca/modelo | < 10 seg |

### Criterio de rechazo

Si un operador dice "no entiendo qué significa este número", el KPI debe rediseñarse antes de implementarse. Los números que confunden no son útiles.

---

## 10. Lo que este módulo NO es

- No es contabilidad oficial. No reemplaza al contador ni a un ERP.
- No incluye impuestos, IVA, depreciación ni cuentas por cobrar.
- No es un sistema de reportes para terceros (bancos, SII, etc.).
- No proyecta el futuro. Solo describe lo que ya ocurrió y lo que hay disponible hoy.

El módulo es una **herramienta de decisión operativa** para que el dueño o encargado pueda actuar con información real, no con intuición.

---

## 11. Views y templates

### 11.1 Dashboard empresa (nivel empresa)

| Elemento | Valor |
|----------|-------|
| **Template** | `templates/taller/desarme/dashboard_asi_va_tu_negocio.html` (nuevo) |
| **View** | `taller/desarme/views_stats.py::dashboard_estadisticas` (nuevo archivo) |
| **URL** | `<pais>/es/desarme/estadisticas/` |
| **URL name** | `desarme:estadisticas` |
| **Datos** | `_kpis_empresa(empresa, periodo)` |
| **Períodos** | semana, mes, trimestre, año |

### 11.2 Panel de vehículo (en Centro de Operaciones)

| Elemento | Valor |
|----------|-------|
| **Partial** | `templates/taller/desarme/partials/_kpis_vehiculo.html` (nuevo) |
| **Helper** | `kpis_vehiculo(vehiculo)` en `views_stats.py` |
| **Include** | Desde `centro_operaciones.html` via `{% include "_kpis_vehiculo.html" with kpis=kpis %}` |

---

## 12. Fase de implementación

Este módulo corresponde a la fase **P2.5** del plan de implementación, entre el Centro de Operaciones (P2) y las etapas físicas (P3).

**Motivo:** El Centro de Operaciones (P2) ya incluye un panel de KPIs básico. La versión completa del dashboard ("Así va tu negocio") requiere que el campo `etapa` exista en `VehiculoDesarme` (P2) para calcular correctamente los estados de los vehículos.

Ver `docs/arquitectura/desarmaduria_v2_plan_p0_p5.md` sección P2.5.
