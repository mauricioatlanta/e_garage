# Desarmaduria v2 — Modelos de Estado
**Fecha:** 2026-08-05  
**Estado:** Diseño técnico. Sin implementación aprobada.  
**Referencia:** `docs/arquitectura/desarmaduria_v2_propuesta.md`

---

## 1. PiezaDesarme — ciclo de vida completo

### 1.1 Diagrama de estados

```
                          ┌─────────────────────────────────────────────────────┐
                          │         CICLO DE VIDA DE PiezaDesarme               │
                          └─────────────────────────────────────────────────────┘

  [SUGERENCIA]
       │
       │  Operador confirma en revisar_vehiculo
       ▼
  ┌──────────────────────────────────────────────────────┐
  │  PiezaDesarme creada                                 │
  │  publicada=False  |  etapa_fisica=CONFIRMADA         │
  │  estado_pieza=DISPONIBLE  |  cantidad≥1              │
  └──────────────────────────────────────────────────────┘
       │
       │  Operador marca como desmontada (scanner_vehiculo)
       ▼
  ┌─────────────────────────┐
  │  etapa_fisica=DESMONTADA│
  │  publicada=False         │
  └─────────────────────────┘
       │
       │  Operador asigna ubicación física
       ▼
  ┌──────────────────────────┐
  │  etapa_fisica=ALMACENADA │
  │  publicada=False          │
  └──────────────────────────┘
       │
       │  Operador ejecuta "Publicar piezas"
       ▼
  ┌──────────────────────────────────────────────────────┐
  │  publicada=True                                      │
  │  → VISIBLE EN KIOSKO / STOREFRONT                    │
  └──────────────────────────────────────────────────────┘
       │
       ├──────────────────────────────────────────────────────────────────┐
       │  Reserva                                        Soft-delete      │
       ▼                                                      ▼           │
  ┌─────────────────────────┐                      ┌─────────────────┐   │
  │  estado_pieza=RESERVADA  │                      │  activo=False   │   │
  └─────────────────────────┘                      │  (no visible)   │   │
       │                │                           └─────────────────┘   │
       │ Liberar        │ Confirmar venta                                  │
       │ reserva        ▼                                                  │
       │   ┌────────────────────────────────────────┐                     │
       │   │  venta parcial:                         │                     │
       │   │    cantidad -= N                        │                     │
       │   │    estado_pieza = DISPONIBLE            │                     │
       │   │                                         │                     │
       │   │  venta total (cantidad → 0):            │                     │
       │   │    cantidad = 0                         │                     │
       │   │    estado_pieza = VENDIDA               │                     │
       │   └────────────────────────────────────────┘                     │
       │                                                                   │
       ▼                                                                   │
  ┌─────────────────────────┐                                             │
  │  estado_pieza=DISPONIBLE │◄────────────────────────────────────────── ┘
  └─────────────────────────┘

  Estados terminales:
  ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
  │  estado=VENDIDA  │   │  estado=SCRAP    │   │  estado=FALTANTE │
  │  cantidad=0      │   │  (cierre vehíc.) │   │  (cierre vehíc.) │
  └──────────────────┘   └──────────────────┘   └──────────────────┘
```

### 1.2 Campos de estado y su semántica

| Campo | Tipo | Valores | Semántica |
|-------|------|---------|-----------|
| `estado_pieza` | CharField | DISPONIBLE, RESERVADA, VENDIDA, DANADA, SCRAP, FALTANTE | Estado comercial de la pieza |
| `activo` | BooleanField | True/False | Soft-delete operacional; `False` = pieza retirada del sistema |
| `publicada` | BooleanField [v2] | True/False | Compuerta del storefront; `False` = no visible aunque esté DISPONIBLE |
| `etapa_fisica` | CharField [v2] | CONFIRMADA, DESMONTADA, ALMACENADA | Tracking del estado físico de la pieza en el taller |
| `cantidad` | PositiveIntegerField | ≥ 0 | Unidades disponibles; 0 significa agotada |

### 1.3 Invariantes del modelo

```
IF cantidad == 0 THEN estado_pieza == VENDIDA
IF estado_pieza == VENDIDA THEN cantidad == 0
IF activo == False THEN publicada == False  (soft-delete implica no visible)
IF publicada == True THEN etapa_fisica IN (DESMONTADA, ALMACENADA)
```

Nota: Los invariantes 3 y 4 son del diseño v2. En datos existentes (pre-v2) no aplican.

### 1.4 Reglas de transición de `estado_pieza`

| Desde | Hacia | Actor | Condición | View |
|-------|-------|-------|-----------|------|
| — | DISPONIBLE | Sistema | Al crear PiezaDesarme | `revisar_vehiculo` |
| DISPONIBLE | RESERVADA | Operador/Cliente | Solicita reserva con tiempo límite | `reservar_pieza` [P4] |
| RESERVADA | DISPONIBLE | Sistema/Operador | Reserva vence o liberada manualmente | cron / panel [P4] |
| DISPONIBLE | VENDIDA | Sistema | `cantidad -= N` y `cantidad == 0` | `finalizar_venta_desde_inventario` |
| RESERVADA | VENDIDA | Sistema | Igual, desde reserva confirmada | `finalizar_venta_desde_inventario` |
| DISPONIBLE | DANADA | Operador | Registra daño post-inspección | `scanner_vehiculo` (futuro) |
| DISPONIBLE | SCRAP | Operador | Al cerrar vehículo, pieza sin salida | `cerrar_vehiculo` [P3] |
| DISPONIBLE | FALTANTE | Operador | Al cerrar vehículo, pieza no localizable | `cerrar_vehiculo` [P3] |

---

## 2. VehiculoDesarme — etapas del proceso

### 2.1 Diagrama de etapas

```
  CREAR VEHÍCULO
       │
       │  POST crear_vehiculo + inicializar_sugerencias()
       ▼
  ┌───────────────────────────────────────────┐
  │  etapa = INGRESADO                        │
  │  Tiene N sugerencias PENDIENTE            │
  │  No tiene PiezaDesarme aún                │
  └───────────────────────────────────────────┘
       │
       │  Operador finaliza revisión en revisar_vehiculo
       │  (todas las sugerencias CONFIRMADA o DESCARTADA)
       ▼
  ┌───────────────────────────────────────────┐
  │  etapa = CONFIRMADO                       │
  │  Tiene N PiezaDesarme con publicada=False  │
  └───────────────────────────────────────────┘
       │
       │  Operador marca todas las piezas como
       │  desmontadas/almacenadas (scanner_vehiculo)
       ▼
  ┌───────────────────────────────────────────┐
  │  etapa = EN_ALMACEN                       │
  │  Piezas físicamente localizadas           │
  │  publicada=False aún                      │
  └───────────────────────────────────────────┘
       │
       │  Operador ejecuta "Publicar piezas"
       │  (al menos 1 pieza publicada)
       ▼
  ┌───────────────────────────────────────────┐
  │  etapa = PUBLICADO                        │
  │  Piezas visibles en kiosko                │
  └───────────────────────────────────────────┘
       │
       │  Primera venta registrada
       ▼
  ┌───────────────────────────────────────────┐
  │  etapa = VENDIENDO                        │
  │  Mix de DISPONIBLE, RESERVADA, VENDIDA    │
  └───────────────────────────────────────────┘
       │
       │  Operador decide cerrar el vehículo
       │  (requiere: ninguna pieza en RESERVADA)
       ▼
  ┌───────────────────────────────────────────┐
  │  etapa = CERRADO  [terminal]              │
  │  VehiculoDesarme.estado_desarme = CERRADO │
  └───────────────────────────────────────────┘
```

### 2.2 Reglas de transición de `etapa`

| Desde | Hacia | Condición | Acción que la dispara |
|-------|-------|-----------|----------------------|
| — | INGRESADO | Al crear vehículo | `crear_vehiculo` POST |
| INGRESADO | CONFIRMADO | No hay sugerencias PENDIENTE | `revisar_vehiculo::finalizar` |
| CONFIRMADO | EN_ALMACEN | Todas las piezas confirmadas tienen `etapa_fisica != CONFIRMADA` | `scanner_vehiculo` (auto-check) |
| EN_ALMACEN | PUBLICADO | Operador publica al menos 1 pieza | `publicar_piezas` |
| PUBLICADO | VENDIENDO | Primera venta exitosa del vehículo | `finalizar_venta_desde_inventario` (auto-check) |
| VENDIENDO | PUBLICADO | No hay piezas VENDIDAS del vehículo | — (no aplica en práctica) |
| PUBLICADO/VENDIENDO | CERRADO | Operador cierra + 0 piezas RESERVADA | `cerrar_vehiculo` |

### 2.3 Relación con `estado_desarme` (campo existente)

`estado_desarme` es el campo existente en el modelo. `etapa` es el campo nuevo v2.

En la fase de transición, ambos coexisten:

| `etapa` (v2) | `estado_desarme` (existente) equivalente |
|-------------|------------------------------------------|
| INGRESADO | INGRESADO |
| CONFIRMADO | DESARMANDO |
| EN_ALMACEN | DESARMANDO |
| PUBLICADO | DESARMADO |
| VENDIENDO | DESARMANDO (o DESARMADO) |
| CERRADO | CERRADO o AGOTADO |

En P5 se puede deprecar `estado_desarme` y usar solo `etapa`. No se toca en P1-P4.

---

## 3. SugerenciaPiezaDesarme — pre-inventario

### 3.1 Diagrama de estados

```
  inicializar_sugerencias()
       │
       ▼
  ┌──────────────────────────────┐
  │  estado = PENDIENTE          │
  │  (creada al hacer el carro)  │
  └──────────────────────────────┘
       │
       ├─────────────────────────┐
       │ confirmar               │ descartar
       ▼                         ▼
  ┌──────────────────┐   ┌───────────────────┐
  │  CONFIRMADA      │   │  DESCARTADA       │
  │  → PiezaDesarme  │   │  (no se crea pieza)│
  │    creada        │   └───────────────────┘
  └──────────────────┘           │
       │                         │ reabrir
       │                         ▼
       │                   ┌──────────────────────────┐
       │                   │  PENDIENTE (de nuevo)    │
       │                   └──────────────────────────┘
       │
       │  (no hay transición desde CONFIRMADA
       │   — la pieza ya existe en BD)
       ▼
  (terminal: la sugerencia queda CONFIRMADA
   y la PiezaDesarme es la fuente de verdad)
```

### 3.2 Reglas de negocio

- Una sugerencia en CONFIRMADA no puede volver a PENDIENTE si ya existe una `PiezaDesarme` asociada.
- Una sugerencia en DESCARTADA puede volver a PENDIENTE hasta que el operador finalice la revisión.
- El botón "Finalizar revisión" solo activa si no hay sugerencias en PENDIENTE.
- Las sugerencias son por vehículo y por empresa (tenant-scoped).

---

## 4. ReservaDesarme (nuevo, P4)

### 4.1 Diagrama de estados

```
  Comprador/Operador solicita reserva
       │
       ▼
  ┌──────────────────────────────────────────────────┐
  │  ReservaDesarme creada                           │
  │  activa=True                                     │
  │  PiezaDesarme.estado_pieza = RESERVADA           │
  │  fecha_expiracion = now() + horas_reserva        │
  └──────────────────────────────────────────────────┘
       │
       ├──────────────────────────────┐
       │ fecha_expiracion alcanzada   │ Operador libera manualmente
       ▼                              ▼
  ┌──────────────────────┐   ┌──────────────────────┐
  │  activa=False        │   │  activa=False        │
  │  PiezaDesarme →      │   │  PiezaDesarme →      │
  │  DISPONIBLE          │   │  DISPONIBLE          │
  └──────────────────────┘   └──────────────────────┘
       
       │ (alternativa) Operador confirma venta
       ▼
  ┌──────────────────────────────────────────────────┐
  │  activa=False                                    │
  │  PiezaDesarme → finalizar_venta_desde_inventario │
  │  → cantidad-=N, estado=VENDIDA si cantidad==0    │
  └──────────────────────────────────────────────────┘
```

---

## 5. Documento / flujo de venta canónico

### 5.1 Relación con PiezaDesarme

```
finalizar_venta_desde_inventario
    │
    ▼
Documento
    │  origen_repuesto = ORIGEN_DESARME (en LineaRepuesto)
    │
    └── LineaRepuesto (×N)
            │  FK → PiezaDesarme
            │  nombre_pieza (snapshot)
            │  cantidad
            │  precio_unitario (negociado)
            │  subtotal
```

El `nombre_pieza` se copia como snapshot porque el operador puede renombrar la pieza después sin afectar documentos históricos.

### 5.2 Qué ocurre con PiezaDesarme después de la venta

```
ANTES:  pieza.cantidad = N, estado_pieza = DISPONIBLE
VENTA:  cantidad_vendida = K

CASO A (K < N):
  pieza.cantidad = N - K
  pieza.estado_pieza = DISPONIBLE  (sin cambio)
  → pieza sigue visible en kiosko si N-K > 0

CASO B (K == N):
  pieza.cantidad = 0
  pieza.estado_pieza = VENDIDA
  → pieza sale del kiosko (cantidad__gt=0 falla)
```

### 5.3 ¿Qué NO puede hacer la venta canónica?

- No puede decrementar más de lo disponible (`_StockInsuficiente` corta la transacción)
- No puede vender una pieza con `estado_pieza=VENDIDA` (validación por estado + cantidad)
- No puede vender una pieza de otra empresa (filtro `empresa=empresa` en `select_for_update`)
- No puede vender sin sesión válida (`session["venta_desde_inventario"]` requerida)

---

## 6. VentaDesarme — flujo legado y límites

### 6.1 Relación con el flujo canónico

```
VentaDesarme (flujo rápido, legado)
    └── LineaVentaDesarme (×N)
            └── FK → PiezaDesarme

Documento (flujo canónico, v2)
    └── LineaRepuesto (×N)
            └── FK → PiezaDesarme
```

Ambos comparten la misma `PiezaDesarme`. Un documento canónico puede vender una pieza que antes fue parte de una VentaDesarme, y viceversa. El stock en `PiezaDesarme.cantidad` es la única fuente de verdad.

### 6.2 Cómo leer datos históricos de VentaDesarme

Para reportes de ingresos históricos de ventas rápidas:
```python
LineaVentaDesarme.objects.filter(
    venta__empresa=empresa,
    pieza__vehiculo_desarme=vehiculo,
).aggregate(total=Sum(F("cantidad") * F("precio_unitario")))
```

Para reportes unificados (v2+):
```python
# Ingresos por Documento (canónico)
LineaRepuesto.objects.filter(
    documento__empresa=empresa,
    origen_repuesto=ORIGEN_DESARME,
    pieza__vehiculo_desarme=vehiculo,
).aggregate(total=Sum("subtotal"))

# Ingresos por VentaDesarme (legado)
LineaVentaDesarme.objects.filter(
    venta__empresa=empresa,
    pieza__vehiculo_desarme=vehiculo,
).aggregate(total=Sum(F("cantidad") * F("precio_unitario")))

# Total combinado: suma de ambos
```

### 6.4 Migración de VentaDesarme a Documento (NO en alcance v2)

No se migran los datos históricos de `VentaDesarme`. Razones:
1. La semántica no es 1:1 (VentaDesarme no tiene número de documento, serie, ni integración contable completa)
2. Los datos históricos son válidos como están para reportes
3. El riesgo de corrupción de datos supera el beneficio

La migración conceptual es: nuevas ventas van SIEMPRE a `Documento + LineaRepuesto`. `VentaDesarme` solo recibe ventas de los flujos legados que aún no han sido actualizados.

---

## 6.3 Qué no registra la venta canónica

Estos costos no están en el modelo y quedan fuera de los KPIs de rentabilidad:
- Costo de mano de obra de desmonte
- Horas operario invertidas
- Costo de almacenaje y espacio físico
- Fletes y transporte

El módulo de estadísticas informa **ganancia bruta** (ingresos − costo de adquisición), no utilidad neta. El operador debe ser consciente de esta limitación.

---

## 7. Estadísticas — modelo de datos de lectura

Las vistas de estadísticas son **de solo lectura**. No escriben nada. Agregan datos de los modelos transaccionales.

### 7.1 Fuentes por KPI

```
"¿Cuánto entró?" (costo)
    VehiculoDesarme.costo_adquisicion
    → Puede ser NULL. Si NULL: KPI incompleto.

"¿Cuánto salió?" (ingresos)
    LineaRepuesto.subtotal
        WHERE pieza.vehiculo_desarme = v
          AND origen_repuesto = ORIGEN_DESARME
          AND documento.estado NOT IN ('ANULADO', 'BORRADOR')
    +
    LineaVentaDesarme.cantidad × precio_unitario
        WHERE pieza.vehiculo_desarme = v
          AND venta.anulada = False
    → Sumar ambos flujos. Nunca elegir uno.
    → Excluir ANULADO y BORRADOR del flujo canónico.

"¿Cuánto queda por recuperar?" (potencial)
    SUM(PiezaDesarme.precio_venta_sugerido × cantidad)
        WHERE vehiculo_desarme = v
          AND estado_pieza IN (DISPONIBLE, RESERVADA)
          AND activo = True
          AND precio_venta_sugerido > 0
    → Excluir piezas con precio=0 o NULL. Contar cuántas se excluyen.

"¿Qué requiere atención?" (alertas)
    costo IS NULL OR costo = 0                         → ALERTA_SIN_COSTO
    pieza.precio = 0 AND activo=True AND publicada=True → ALERTA_SIN_PRECIO
    etapa=PUBLICADO AND dias>30 AND COUNT(ventas)=0    → ALERTA_ESTANCADO
    etapa IN (CONFIRMADO, EN_ALMACEN) AND dias>7        → ALERTA_SIN_PUBLICAR
    ReservaDesarme.activa=True AND expiracion<now()    → ALERTA_RESERVA_VENCIDA
```

### 7.2 Invariantes de las queries de estadísticas

- Siempre filtrar por `empresa` antes de cualquier agregación (aislamiento tenant)
- Nunca mostrar ROI cuando `costo = 0` o NULL (división por cero → retornar `None`, no `0`)
- `ganancia_bruta` retorna `None` (no `0`) cuando `costo_adquisicion` es NULL — NULL no se interpreta como cero
- `documento.estado NOT IN ('ANULADO', 'BORRADOR')` es obligatorio en toda query de ingresos
- `venta.anulada = False` es obligatorio en toda query sobre VentaDesarme
- El potencial restante incluye piezas NO publicadas (para reflejar valor total disponible en cualquier etapa)
- El potencial restante es una **estimación al precio sugerido**, no al precio de venta real

### 7.3 No hay modelo nuevo para estadísticas

Las estadísticas se calculan en tiempo real sobre los modelos existentes. No hay tabla de caché ni modelo `EstadisticaVehiculo`. Si el rendimiento es problemático con muchos vehículos, se puede añadir caché de query en P5.

---

## 8. Filtro base del storefront — evolución

### v1 (pre-P0)
```python
PiezaDesarme.objects.filter(
    empresa=empresa,
    activo=True,
    estado_pieza=DISPONIBLE,
)
```
Bug: piezas con `cantidad=0` y estado erróneo aparecían en el storefront.

### v1.1 (P0 — implementado)
```python
PiezaDesarme.objects.filter(
    empresa=empresa,
    activo=True,
    estado_pieza=DISPONIBLE,
    cantidad__gt=0,
)
```
Correcto pero no distingue piezas publicadas de piezas en proceso.

### v2 (P1 — pendiente)
```python
PiezaDesarme.objects.filter(
    empresa=empresa,
    activo=True,
    publicada=True,
    estado_pieza=DISPONIBLE,
    cantidad__gt=0,
)
```
Filtro canónico final. Solo piezas que el operador decidió publicar explícitamente.

---

## 9. Referencias

| Documento | Contenido |
|-----------|-----------|
| `desarmaduria_v2_propuesta.md` | Problema, decisión central, principios, impacto por capa |
| `desarmaduria_v2_mapa_modulos.md` | Módulos por etapa, templates, URLs, dependencias |
| `desarmaduria_v2_plan_p0_p5.md` | Fases de implementación P0–P5, criterios de entrada/salida |
| `desarmaduria_v2_estadisticas_negocio.md` | KPIs, fórmulas, fuentes de datos, calidad de datos, queries |
| `desarmaduria_v2_experiencia_humana.md` | Lenguaje, estados emocionales, criterios de aceptación humana |
