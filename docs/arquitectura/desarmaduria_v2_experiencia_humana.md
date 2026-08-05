# Desarmaduria v2 — Experiencia Humana
**Fecha:** 2026-08-05  
**Estado:** Diseño técnico. Sin implementación aprobada.  
**Referencia:** `docs/arquitectura/desarmaduria_v2_propuesta.md`, `desarmaduria_v2_estadisticas_negocio.md`

---

## 1. Quién usa este sistema

El operador de una desarmaduria en Latinoamérica es generalmente:
- Dueño del taller o encargado de turno
- Sin formación contable formal
- Acostumbrado a tomar decisiones por intuición y experiencia
- Con acceso al sistema desde el computador del taller, no desde celular
- Bajo presión de tiempo: clientes esperando, teléfono sonando

Este sistema debe ser útil para esa persona. No para un analista de datos.

---

## 2. Los estados emocionales del operador

El diseño debe responder a estos estados reales:

| Estado emocional | Pregunta que tiene | Qué necesita el sistema |
|-----------------|--------------------|------------------------|
| **Incertidumbre** al comprar un auto | "¿Le sacaré provecho a esto?" | Registro rápido de costo + estimación de valor esperado |
| **Presión** al recibir el auto | "¿Cuándo lo tengo listo para vender?" | Flujo claro por etapas, sin pantallas superfluas |
| **Duda** al publicar | "¿A qué precio pongo esto?" | Precio sugerido visible, historial de precios similares (futuro) |
| **Ansiedad** si no vende | "¿Por qué no se está vendiendo?" | Alerta de baja rotación con sugerencia de acción |
| **Satisfacción** al vender | "¿Gané o perdí con este auto?" | Cálculo claro de ROI al instante |
| **Control** cuando todo va bien | "¿Cómo va mi negocio esta semana?" | Dashboard de un vistazo, sin buscar datos |

---

## 3. Principios de experiencia para este módulo

### 3.1 Una pantalla, una tarea

El operador no debe adivinar dónde ir para hacer algo. El Centro de Operaciones muestra **exactamente** qué puede hacer según el estado actual del vehículo. No más, no menos.

### 3.2 El sistema habla primero

Si hay algo urgente (reserva vencida, pieza sin precio, auto sin actividad), el sistema lo dice proactivamente en el bloque "Requiere atención". El operador no tiene que buscar problemas.

### 3.3 Las cifras tienen contexto

Un número solo no sirve. Cada KPI incluye:
- El número
- Lo que significa en lenguaje natural
- La acción sugerida si aplica

**Mal:** `ROI: 87%`  
**Bien:** `Recuperaste el 87% de lo que pagaste. Te faltan $390.000 para cubrir la inversión.`

### 3.4 Los colores no son decorativos

| Color | Significado | Cuándo usarlo |
|-------|------------|---------------|
| Verde | Todo bien, nada que hacer | ROI ≥ 100%, stock saludable |
| Amarillo | Atención, pero no urgente | ROI 50–99%, baja rotación leve |
| Rojo | Acción requerida | Reserva vencida, ROI < 50%, pieza sin precio publicada |
| Gris | Datos incompletos | Costo no registrado, precio en 0 |

### 3.5 Las alertas tienen botón

Cada alerta en "Requiere atención" tiene un botón de acción directa. No solo describe el problema — ofrece el camino para resolverlo.

```
⚠ 14 piezas sin precio registrado
   [Ver piezas sin precio →]
```

```
⚠ Hilux 2018 lleva 32 días publicado sin ventas
   [Revisar precios →]  [Ver en kiosko →]
```

---

## 4. Flujo de experiencia — primer vehículo de un operador nuevo

Este es el recorrido ideal desde cero:

```
1. CREAR VEHÍCULO
   Ingresa marca, modelo, año, patente.
   Ingresa costo de compra → "¿Cuánto pagaste por él?"
   Selecciona daños en el inspector SVG.
   Guarda → ve el Centro de Operaciones.

2. CENTRO DE OPERACIONES — etapa INGRESADO
   Ve: "Tienes 34 piezas sugeridas. Confirma cuáles desmontar."
   Acción disponible: [Revisar piezas →]

3. REVISAR PIEZAS
   Ve la lista por zona. Confirma las que tiene, descarta las que no.
   Asigna precio a cada una o usa el precio sugerido.
   Termina → botón "Finalizar revisión".

4. CENTRO DE OPERACIONES — etapa CONFIRMADO
   Ve: "23 piezas confirmadas. Valor estimado: $1.800.000."
   Ve: "Potencial: 60% de ganancia si vendes todo."
   Acción disponible: [Publicar piezas →]

5. PUBLICAR
   Revisa precios una vez más.
   Publica todas o selecciona.
   → Piezas aparecen en kiosko.

6. CENTRO DE OPERACIONES — etapa PUBLICADO
   Ve: "23 piezas publicadas. Primera venta: 0 ventas aún."
   Alerta si pasan 7 días sin venta.

7. VENDER
   Cliente llega o llama.
   Operador entra a inventario inteligente, selecciona piezas, confirma venta.
   → Documento generado automáticamente.

8. PANEL DE KPIs (actualizado en tiempo real)
   "Generaste $350.000 hoy. Recuperaste el 23% del Hilux."
   "Te faltan $2.310.000 para cubrir lo que pagaste."
   (Nota: el sistema no proyecta plazos ni velocidades — solo describe el estado actual.)

9. CERRAR VEHÍCULO (cuando ya no quedan piezas)
   → KPIs finales: ¿cuánto generó? ¿cuánto quedó sin vender?
   → Historial disponible en dashboard empresa.
```

---

## 5. Diseño del módulo "Así va tu negocio"

### 5.1 Jerarquía de información

```
NIVEL 1 — De un vistazo (< 3 segundos)
├── Inventario activo total
├── Ingresos del mes
└── Alertas urgentes (número)

NIVEL 2 — Con intención (< 15 segundos)
├── Desglose por vehículo (barra de progreso)
├── Alertas con acción directa
└── Tendencia mes anterior vs actual

NIVEL 3 — Análisis (< 2 minutos)
├── ROI por marca/modelo
├── Piezas más vendidas
└── Comparativa entre vehículos
```

### 5.2 Qué NO mostrar en el nivel 1

- Porcentajes sin contexto ("67%")
- Tablas con más de 5 columnas
- Gráficos de línea de tendencia (requieren conocimiento previo)
- Jerga: "Margen bruto", "Tasa de rotación", "ARPU"

### 5.3 Progresión del dashboard según madurez del sistema

El dashboard se adapta a cuántos datos tiene disponibles:

**Estado vacío (empresa nueva, 0 vehículos):**
```
"Cuando registres tu primer vehículo, aquí verás cómo va tu negocio."
[Agregar primer vehículo →]
```

**Estado parcial (1–3 vehículos, sin costo registrado):**
```
"Tienes 3 vehículos activos. Agrega el costo de compra para ver tu rentabilidad."
[Completar datos →]
```

**Estado completo (datos suficientes):**
Dashboard completo con todos los KPIs.

---

## 6. Alertas — catálogo completo

| Código | Condición | Mensaje visible | Acción sugerida |
|--------|-----------|----------------|-----------------|
| `ALERTA_SIN_COSTO` | `costo_adquisicion IS NULL` | "X vehículos sin costo registrado" | [Completar costos →] |
| `ALERTA_SIN_PRECIO` | pieza activa con precio=0 | "N piezas sin precio — no están en el potencial" | [Ver piezas →] |
| `ALERTA_ESTANCADO` | PUBLICADO > 30 días sin ventas | "Auto X lleva N días sin ventas" | [Revisar precios →] |
| `ALERTA_SIN_PUBLICAR` | CONFIRMADO/EN_ALMACEN > 7 días | "Auto X aún no está publicado" | [Publicar →] |
| `ALERTA_RESERVA_VENCIDA` | ReservaDesarme vencida activa | "Reserva vencida de N horas" | [Revisar →] |
| `ALERTA_PRECIO_BAJO` | precio < 50% del promedio de piezas similares | (futuro, requiere datos comparativos) | — |

---

## 7. Casos límite de experiencia

### 7.1 El operador no registró el costo
El sistema no bloquea ninguna funcionalidad. Solo omite los KPIs que dependen del costo y muestra un aviso amable en su lugar.

### 7.2 El vehículo tiene piezas en ambos flujos de venta (canónico + legado)
El sistema suma ambos sin que el operador lo note. El total es correcto.

### 7.3 El operador cerró un vehículo con piezas disponibles
El cierre requiere decisión explícita (SCRAP o FALTANTE). El sistema no permite cerrar con piezas en RESERVADA. El KPI final refleja el valor de lo que quedó sin vender.

### 7.4 El operador tiene 0 ventas en el mes
El dashboard no muestra "-100% vs mes anterior". Muestra "Sin ventas registradas este mes" y no calcula variación porcentual sobre base cero.

---

## 8. Criterios de aceptación — experiencia humana

Antes de considerar el módulo completo, validar con al menos un operador real:

- [ ] Puede leer cuánto generó su negocio este mes sin abrir ningún submenú
- [ ] Puede identificar el vehículo menos rentable en menos de 10 segundos
- [ ] Puede saber si una pieza específica tiene precio registrado
- [ ] Comprende la diferencia entre "inventario disponible" y "potencial si vendes todo"
- [ ] Puede resolver una alerta (reserva vencida, pieza sin precio) en 2 clics o menos
- [ ] No pregunta "¿qué significa este número?" en ningún KPI del nivel 1

Si alguno falla, rediseñar ese KPI antes de implementar.
