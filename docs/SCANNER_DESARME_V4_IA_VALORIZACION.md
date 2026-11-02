# Scanner Desarme v4 — IA de valorización de piezas

Documento de diseño para incorporar **sugerencias de precio inteligentes** en el scanner, de forma realista y aplicable sobre lo ya construido en v2/v3. No se trata de “IA por moda”, sino de que el sistema **sugiera precios útiles automáticamente** a partir de datos reales.

---

## 1. Objetivo

Cuando el usuario abra el scanner, el sistema **ya tenga sugerencias de precio** para cada pieza. El operador solo **revisa y ajusta**.

**Flujo actual (v2/v3):**
```
crear vehículo → scanner → poner precio manual
```

**Flujo objetivo (v4):**
```
crear vehículo → scanner → sugerencias automáticas → depurar → ajustar → inventario listo
```

**Tiempo objetivo:** 2 a 4 minutos por vehículo.

---

## 2. Problema que resolvemos

Asignar precio manualmente a decenas de piezas consume tiempo y es propenso a errores. La idea es que el sistema **proponga un precio sugerido basado en datos reales** y el operador solo confirme o fine-tune.

---

## 3. Orígenes de datos para sugerir precio

No se requiere ML complejo en una primera versión. Se usan **3 fuentes simples**.

### Fuente 1 — Catálogo base

**Ya existe:** `taller/desarme/catalogo_piezas.py`.

Cada ítem del catálogo tiene: `codigo`, `nombre`, `zona`, `precio_base`. Al generar el inventario, las piezas se crean con ese `precio_base` como primera referencia.

| Ejemplo   | Precio base (catálogo) |
|----------|-------------------------|
| Alternador | $90.000               |
| Faro      | (según zona en catálogo) |
| Motor completo | $450.000         |

**Uso:** Si la pieza viene del catálogo, `precio_referencia` = precio_base del catálogo. Si no, se puede usar el **promedio de la zona** (otras piezas del mismo vehículo o del catálogo en esa zona).

### Fuente 2 — Historial de ventas

Base de datos interna: cuando una pieza se vende (o se marca con precio final), se registra ese precio.

**Ejemplo:**

- Pieza: Alternador (mismo código o nombre normalizado)
- Últimas 6 ventas: 75k, 82k, 80k, 79k, 85k
- **Precio sugerido desde historial:** promedio o mediana (ej. ~82k)

Requiere una tabla **PrecioHistoricoPieza** (o equivalente) que almacene: pieza/código, modelo, marca, precio, fecha, empresa. Ver sección 15.

### Fuente 3 — Precios del mismo modelo de vehículo

Si la empresa ya desarmó otros vehículos del **mismo modelo** (ej. Hilux 2017, Hilux 2016, Hilux 2018), se pueden usar los precios que ya asignaron a piezas con el mismo código/nombre.

**Ejemplo:** Para “Alternador” en un Hilux 2019, usar precios de Alternador en Hilux 2017/2016/2018 ya valorizados.

Esto es muy potente porque refleja el mercado real de esa pieza en ese modelo.

---

## 4. Algoritmo simple de sugerencia (v4, sin ML)

**Primera versión:**

```
precio_sugerido =
  0.40 * promedio_historial_ventas   (si existe)
+ 0.40 * promedio_mismo_modelo       (si existe)
+ 0.20 * precio_catalogo             (si existe)
```

**Reglas de fallback:**

| Condición              | Acción                                      |
|------------------------|---------------------------------------------|
| No existe historial    | Usar solo catálogo + mismo modelo (50/50 o 100% catálogo) |
| No existe mismo modelo | Usar historial + catálogo                   |
| No existe catálogo     | Usar **promedio de la zona** (mismo vehículo o otros) |
| Ninguna fuente         | Dejar sin sugerencia o usar promedio zona   |

Pesos (40/40/20) son configurables; se pueden ajustar según calidad de datos.

---

## 5. Visualización en el scanner

### Al editar precio (modal o inline)

Mostrar:

- **Precio actual:** $90.000
- **Sugerido:** $85.000 (y opcionalmente origen: “Historial + modelo”)

Botón rápido: **[Usar sugerido]** que rellena el campo con el valor sugerido y permite guardar.

### En las cards (vista normal)

Cada card puede mostrar:

- **Precio:** $90.000 (actual)
- **Sugerido:** $85.000 (si existe y difiere, o siempre en modo “mostrar sugerencias”)

Si el precio está muy fuera del rango sugerido (ver reglas de alerta), mostrar:

- ⚠ **Precio alto** (vs mercado/sugerido)
- ⚠ **Precio bajo** (vs mercado/sugerido)

---

## 6. Reglas de alerta

Comparar **precio actual** vs **promedio/sugerido** (según lo que se use en el algoritmo):

| Condición                    | Aviso en UI        |
|-----------------------------|--------------------|
| Precio > ~40% sobre promedio | **Precio alto vs mercado** |
| Precio < ~40% bajo promedio  | **Precio bajo**    |

Umbral (40%) configurable. Ayuda a operadores nuevos a no errar por mucho.

---

## 7. Endpoints nuevos

### 7.1 Sugerencia por pieza

**GET** `/api/piezas/<id>/precio-sugerido/`

**Respuesta 200:**

```json
{
  "sugerido": 85000,
  "catalogo": 80000,
  "historial": 83000,
  "modelo": 87000,
  "origen": "historial,modelo,catalogo"
}
```

- Campos opcionales: si no hay historial, `historial` puede ser `null`. El frontend usa los que vengan.
- `origen`: resumen de fuentes usadas para el cálculo (auditoría/claridad).

### 7.2 Sugerencias en lote (más eficiente para el scanner)

**POST** `/api/piezas/precios-sugeridos/`

**Payload:**

```json
{
  "ids": [1, 2, 3]
}
```

**Respuesta 200:**

```json
{
  "1": 85000,
  "2": 45000,
  "3": 1200000
}
```

O con más detalle por pieza (opcional):

```json
{
  "1": { "sugerido": 85000, "catalogo": 80000, "historial": 83000 },
  "2": { "sugerido": 45000, "catalogo": 45000 }
}
```

Así el frontend puede cargar **todas las sugerencias al abrir el scanner** en una sola petición.

---

## 8. Modelo de datos necesario

### 8.1 Ampliación de PiezaDesarme (recomendado para v4)

| Campo              | Tipo     | Uso                                                                 |
|--------------------|----------|---------------------------------------------------------------------|
| `precio_referencia`| Decimal  | Precio del catálogo o referencia (opcional, nullable)             |
| `precio_sugerido`  | Decimal  | Última sugerencia calculada (cache; opcional)                      |
| `origen_precio`    | CharField| Origen del precio actual: `catalogo` \| `historial` \| `modelo` \| `manual` |

`origen_precio` permite auditoría: saber si el operador usó sugerencia o puso precio manual.

### 8.2 Tabla de historial (base de la “IA”)

**Antes de implementar sugerencias avanzadas**, conviene crear una tabla para almacenar precios reales:

**PrecioHistoricoPieza** (o nombre similar):

| Campo      | Tipo      | Uso                                      |
|------------|-----------|------------------------------------------|
| pieza      | FK o ref  | Pieza/registro que se vendió o valorizó  |
| codigo     | CharField | Código de pieza (para matchear sin FK)   |
| nombre     | CharField | Nombre (normalizado si aplica)          |
| marca      | FK o str  | Marca del vehículo                       |
| modelo     | FK o str  | Modelo del vehículo                     |
| precio     | Decimal   | Precio de venta o precio asignado        |
| fecha      | DateTime  | Fecha del hecho                         |
| empresa    | FK        | Tenant                                  |

Este dataset es la **base para historial de ventas** y “mismo modelo”. Sin esta tabla, en v4 solo se pueden usar catálogo y (si existe) mismo vehículo/zona.

---

## 9. Mejora UX: aplicar sugerencias en lote

**Botón global en el scanner:**

**Aplicar sugerencias**

Opciones (dropdown o dos botones):

1. **Solo piezas sin precio**  
   Para todas las piezas con `precio_venta_sugerido` NULL o 0, llamar al endpoint de sugerencias y guardar (o pre-rellenar y que el usuario confirme).

2. **Toda la zona**  
   Para las piezas de la zona actual (filtro activo), aplicar sugerencias.

Implementación posible:

- Llamar `POST /api/piezas/precios-sugeridos/` con los ids correspondientes.
- Luego `POST /api/piezas/bulk-precio/` no aplica (eso multiplica). Hace falta un **“bulk asignar precio”** que reciba `{ "ids": [1,2,3], "precios": { "1": 85000, "2": 45000 } }` o un endpoint **“aplicar sugerencias”** que internamente asigne `precio_sugerido` a `precio_venta_sugerido` para esos ids.

Alternativa más simple: en el frontend, para cada id sin precio, obtener sugerido y llamar a `POST /api/piezas/<id>/precio/` con ese valor (menos eficiente pero reutiliza lo existente).

---

## 10. Dashboard futuro (post-v4)

Con sugerencias y precios reales se puede mostrar:

- **Vehículo Hilux 2017**
  - Valor potencial **sugerido** (suma de sugeridos): $4.5M
  - Valor **actual** (suma de precios asignados): $4.8M

Esto permite evaluar si la valorización quedó por encima o por debajo de la sugerencia.

---

## 11. Roadmap de IA realista

| Versión | Contenido                                           |
|---------|-----------------------------------------------------|
| **v4**  | IA simple: catálogo + historial + mismo modelo, pesos fijos, sin ML |
| **v5**  | Modelo de predicción básico (ej. regresión o promedios por segmento) |
| **v6**  | Integración precios de mercado externos (APIs, scrapers, etc.)      |

v4 se apoya en datos internos y reglas claras; v5/v6 pueden ir añadiendo complejidad sin cambiar el flujo del scanner.

---

## 12. Ventaja competitiva

La mayoría del software de desarmaduría **no sugiere precios**. Con v4, eGarage puede:

- Sugerir precios automáticamente a partir de catálogo, historial y mismo modelo.
- Reducir tiempo de valorización a 2–4 minutos por vehículo.
- Dar alertas cuando el precio se desvía mucho del rango esperado.

Eso es muy potente comercialmente.

---

## 13. Flujo final ideal (v4)

```
crear vehículo
    ↓
scanner (carga sugerencias en lote)
    ↓
sugerencias de precio automáticas visibles en cards
    ↓
depurar faltantes / dañadas
    ↓
ajustar precios (usar sugerido donde aplique)
    ↓
inventario listo
```

**Tiempo total objetivo:** 2 a 4 minutos por vehículo.

---

## 14. Checklist técnico para v4

### Backend

| Item | Descripción | Estado |
|------|-------------|--------|
| Tabla PrecioHistoricoPieza | pieza/codigo, modelo, marca, precio, fecha, empresa | Pendiente |
| GET precio-sugerido | `/api/piezas/<id>/precio-sugerido/` → sugerido, catalogo, historial, modelo | Pendiente |
| POST precios-sugeridos | `/api/piezas/precios-sugeridos/` body `{ ids }` → mapa id → sugerido | Pendiente |
| Lógica de sugerencia | 40% historial + 40% modelo + 20% catálogo; fallbacks según sección 4 | Pendiente |
| Campos PiezaDesarme | precio_referencia, precio_sugerido, origen_precio (opcional) | Pendiente |
| Registro en historial | Al guardar precio o al marcar venta, insertar en PrecioHistoricoPieza | Pendiente |

### Frontend

| Item | Descripción | Estado |
|------|-------------|--------|
| Carga al abrir scanner | Llamar POST precios-sugeridos con todos los ids del vehículo | Pendiente |
| Card: mostrar sugerido | Línea “Sugerido: $X” y botón [Usar sugerido] al editar | Pendiente |
| Alertas precio alto/bajo | Si precio > o < ~40% vs sugerido/promedio, mostrar aviso en card | Pendiente |
| Botón “Aplicar sugerencias” | Opciones: solo sin precio, o por zona | Pendiente |
| i18n / country_url | Mantener en todos los textos y enlaces | — |

---

## 15. Siguiente paso recomendado (antes de IA)

Para que la “IA” tenga base real:

1. **Crear la tabla PrecioHistoricoPieza** (o equivalente) con: pieza/código, modelo, marca, precio, fecha, empresa.
2. **Definir el momento de registro:** por ejemplo al guardar `precio_venta_sugerido` en una pieza DISPONIBLE, o cuando se marca como VENDIDA (precio de venta).
3. Con esa tabla poblada, implementar los endpoints de sugerencia (GET por pieza, POST en lote) y el algoritmo de la sección 4.

Sin historial, v4 puede arrancar solo con **catálogo + mismo modelo** (otros vehículos del mismo modelo ya valorizados en la empresa), y dejar preparado el flujo para cuando exista historial.

---

## Relación con Scanner v3

- v3 (PUM) define: estados, métricas en vivo, bulk estado/precio, panel comercial, filtros, revisión.
- v4 **extiende** el mismo scanner con: **sugerencias de precio**, **orígenes de datos**, **alertas** y **aplicar sugerencias en lote**, sin sustituir la UI actual.
