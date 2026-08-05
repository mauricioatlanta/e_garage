# Desarmaduria v2 — P1.5 · Diseño del Centro de Operaciones
**Fecha:** 2026-08-05  
**Estado:** Diseño validado. Sin implementación. Prerequisito de P2.  
**Alcance:** Solo diseño — sin código, sin modelos, sin migraciones.  
**Referencia:** `desarmaduria_v2_propuesta.md`, `desarmaduria_v2_experiencia_humana.md`, `desarmaduria_v2_estadisticas_negocio.md`

---

## 1. Propósito y filosofía

> eGarage no está administrando repuestos. Está administrando la vida completa de un vehículo desde que entra al patio hasta que genera su última utilidad.

El Centro de Operaciones es la materialización de esa idea. Es la pantalla que el operador verá cientos de veces al día. No es un formulario, no es un listado, no es un dashboard genérico. Es la **ficha viva** de un vehículo: muestra su historia, su estado actual, su salud financiera, y —lo más importante— qué hacer ahora mismo.

Si esta pantalla queda bien diseñada, el resto del sistema se ordena alrededor de ella. Si queda mal, P2 termina adaptándose a una pantalla en lugar de que la pantalla refleje el flujo real del negocio.

Esta es la razón de P1.5: diseñar antes de implementar.

---

## 2. Principios de diseño (específicos de esta pantalla)

### 2.1 Una pantalla, una historia

El Centro de Operaciones no es un menú de opciones. Es el hilo narrativo de un vehículo: qué pasó, dónde está ahora, qué viene después. El operador no debería tener que reconstruir ese hilo mentalmente — la pantalla lo cuenta sola.

### 2.2 El peso visual sigue la urgencia

El elemento más urgente ocupa el mayor espacio visual. En la mayoría de los estados, ese elemento es "Siguiente acción". En estados avanzados (VENDIENDO), ese elemento es el progreso financiero. El diseño nunca distribuye peso visual de manera uniforme.

### 2.3 Los números hablan primero

Cada KPI visible habla en español de negocio, no en jerga financiera. No hay "margen bruto". Hay "cuánto te queda por recuperar".

### 2.4 La pantalla no miente cuando faltan datos

Si el operador no registró el costo, la pantalla dice "Sin costo registrado" — no muestra cero, no muestra 100% de ganancia, no omite el KPI silenciosamente. El dato faltante es un estado explícito, no un error.

### 2.5 Cada alerta tiene salida

Ninguna alerta es informativa sin más. Cada alerta tiene un botón que lleva al operador exactamente al lugar donde puede resolver el problema. Describir un problema sin ofrecer la salida es transferir ansiedad, no información.

---

## 3. URL y punto de entrada

El Centro de Operaciones **es** la evolución de `ver_vehiculo.html`. No es una pantalla nueva en una URL nueva. La misma URL que hoy muestra el detalle del vehículo, post-P2 mostrará el Centro de Operaciones.

```
/cl/es/desarme/vehiculos/{pk}/   →   Centro de Operaciones
```

El título de la página es el nombre del vehículo (marca + modelo + año), no "Centro de Operaciones". El operador trabaja con su Hilux, no con un "centro".

---

## 4. Anatomía de la pantalla

### Wireframe general — desktop (1200px+)

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  [←]  TOYOTA HILUX D4D 2018  ·  ABC-1234                     [Cerrar veh.] ║
║        ● PUBLICADO   —   28 días en patio desde el 08/07                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  INGRESADO ──── CONFIRMADO ──── EN ALMACÉN ──●─ PUBLICADO ──── VENDIENDO   ║
║  08 jul        10 jul           12 jul          15 jul                       ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  ┌──────────────────────────────────────────────────────────────────────┐   ║
║  │  ▶  SIGUIENTE ACCIÓN                                                  │   ║
║  │     28 días publicado sin ventas. Es probable que los precios estén   │   ║
║  │     fuera del rango del mercado o que falten fotos en las piezas.     │   ║
║  │                                                                        │   ║
║  │            [Revisar precios →]       [Ver en kiosko →]               │   ║
║  └──────────────────────────────────────────────────────────────────────┘   ║
║                                                                              ║
║  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐ ┌──────────────┐ ║
║  │    PAGASTE     │ │    ENTRARON    │ │  RECUPERASTE   │ │  AÚN FALTA   │ ║
║  │  $ 3.200.000   │ │   $ 840.000   │ │      26%       │ │ $ 2.360.000  │ ║
║  │                │ │               │ │  ████░░░░░░░   │ │              │ ║
║  └────────────────┘ └────────────────┘ └────────────────┘ └──────────────┘ ║
║                                                                              ║
║  ┌─────────────────────────────────┐  ┌─────────────────────────────────┐  ║
║  │  PIEZAS                         │  │  REQUIERE ATENCIÓN               │  ║
║  │                                 │  │                                  │  ║
║  │  23  publicadas                 │  │  ⚠ 14 piezas sin precio          │  ║
║  │   7  en proceso                 │  │     No contribuyen al potencial.  │  ║
║  │   4  vendidas                   │  │     [Ver piezas sin precio →]    │  ║
║  │                                 │  │                                  │  ║
║  │  Potencial restante:            │  │  ⚠ 28 días sin actividad de venta│  ║
║  │  $ 1.820.000                    │  │     [Revisar precios →]          │  ║
║  │                                 │  │                                  │  ║
║  │  [Ver inventario completo →]    │  │                                  │  ║
║  └─────────────────────────────────┘  └─────────────────────────────────┘  ║
║                                                                              ║
║  ──────────────────────────────────────────────────────────────────────────  ║
║  [Registrar venta]   [Publicar piezas]   [Ver en kiosko]   [Más acciones ▾] ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 5. Zonas de la pantalla — detalle de cada componente

### 5.1 Cabecera viva

```
TOYOTA HILUX D4D 2018  ·  ABC-1234             [Cerrar vehículo]
● PUBLICADO  —  28 días en patio desde el 08/07
```

**Reglas:**
- Marca + modelo + año siempre presentes. Patente si existe.
- El estado (`etapa`) se muestra como badge de color (ver §5.1a).
- "Días en patio" se cuenta desde `fecha_ingreso` hasta hoy. Siempre visible.
- El botón "Cerrar vehículo" aparece solo en VENDIENDO y con piezas en 0. En otros estados se llama "Archivar" y requiere confirmación explícita.

**5.1a — Colores del badge de etapa:**

| Etapa | Color badge | Semántica |
|-------|------------|-----------|
| INGRESADO | Gris | Recién llegó |
| CONFIRMADO | Azul | En proceso |
| EN_ALMACEN | Azul | En proceso |
| PUBLICADO | Verde | Activo en kiosko |
| VENDIENDO | Verde intenso | Generando ingresos |
| CERRADO | Gris oscuro | Histórico |

---

### 5.2 Barra de progreso con historia

```
INGRESADO ──── CONFIRMADO ──── EN ALMACÉN ──●─ PUBLICADO ──── VENDIENDO
08 jul          10 jul           12 jul        15 jul
```

**Reglas:**
- Cada etapa completada muestra la fecha en que se entró a esa etapa.
- La etapa actual tiene el punto `●` y queda resaltada.
- Las etapas futuras son visibles pero tenues (gris claro) — el operador ve el camino completo.
- CERRADO aparece al final fuera del flujo normal (flecha distinta o separado visualmente).
- En mobile: la barra colapsa a "Etapa 3 de 5: PUBLICADO" con flecha para expandir.

**Lo que esta barra NO hace:**
- No muestra fechas estimadas para etapas futuras.
- No proyecta velocidad ni plazos.
- No dice "llevas X días en esta etapa" (esa información está en la cabecera).

---

### 5.3 Bloque "Siguiente acción" — la zona de mayor peso visual

Este bloque es la razón de ser de la pantalla. El operador llega aquí y en menos de 3 segundos sabe qué hacer.

**Estructura:**
```
┌──────────────────────────────────────────────────────────┐
│  ▶  SIGUIENTE ACCIÓN                                      │
│     [Texto en lenguaje de negocio: qué pasa y qué hacer] │
│                                                           │
│            [Botón acción principal →]   [Secundaria →]   │
└──────────────────────────────────────────────────────────┘
```

**Reglas:**
- Siempre hay una acción principal. Nunca está vacío el bloque (incluso CERRADO muestra "Este vehículo está cerrado. Puedes ver el resumen final." con botón al historial).
- Máximo dos botones. El principal va a la derecha y tiene más peso visual.
- El texto no dice qué hacer en imperativo seco ("Haz X"). Explica brevemente por qué antes de qué. Dos líneas máximo.
- El color del bloque cambia según urgencia: verde (todo bien), amarillo (atención), rojo (acción urgente).

La tabla completa de acciones por estado está en §6.

---

### 5.4 KPIs financieros — cuatro tarjetas

```
┌────────────────┐ ┌────────────────┐ ┌────────────────┐ ┌──────────────┐
│    PAGASTE     │ │    ENTRARON    │ │  RECUPERASTE   │ │  AÚN FALTA   │
│  $ 3.200.000   │ │   $ 840.000   │ │      26%       │ │ $ 2.360.000  │
│                │ │               │ │  ████░░░░░░░   │ │              │
└────────────────┘ └────────────────┘ └────────────────┘ └──────────────┘
```

**Las cuatro tarjetas:**

| # | Etiqueta | Valor | Fuente | Estado si falta dato |
|---|----------|-------|--------|---------------------|
| 1 | PAGASTE | `costo_adquisicion` | `VehiculoDesarme.costo_adquisicion` | "Sin registro" (gris) |
| 2 | ENTRARON | `ingresos_totales` | Suma de líneas de venta activas | "$0" (gris) si 0 ventas |
| 3 | RECUPERASTE | `pct_recuperado` | `(ingresos/costo)*100` | "—" si costo null |
| 4 | AÚN FALTA | `falta_recuperar` | `costo - ingresos` | "—" si costo null |

**Tarjeta 3 (RECUPERASTE) — variantes:**

| % recuperado | Barra | Color |
|-------------|-------|-------|
| < 50% | ██░░░░░░░░ | Rojo |
| 50–99% | ████░░░░░ | Amarillo |
| 100–149% | ██████████ | Verde |
| ≥ 150% | ██████████ + "¡Ganancia!" | Verde intenso |

**Cuándo mostrar las tarjetas:**
- Las 4 tarjetas aparecen desde INGRESADO. No esperan a PUBLICADO.
- Si `costo_adquisicion` es null, las tarjetas 3 y 4 muestran "—" con un link "Agregar costo →".
- Si `ingresos_totales` es 0, la tarjeta 2 muestra "$0" en gris (no "Sin ventas" — eso es una alerta separada).

---

### 5.5 Resumen de piezas

```
┌─────────────────────────────────┐
│  PIEZAS                         │
│                                 │
│  23  publicadas       verde     │
│   7  en proceso       gris      │
│   4  vendidas         azul      │
│   0  sin precio       ← rojo    │
│                                 │
│  Potencial restante:            │
│  $ 1.820.000                    │
│                                 │
│  [Ver inventario completo →]    │
└─────────────────────────────────┘
```

**Conteos:**

| Fila | Condición de filtro | Color |
|------|---------------------|-------|
| publicadas | `publicada=True, estado=DISPONIBLE, activo=True` | Verde |
| en proceso | `publicada=False, estado=DISPONIBLE, activo=True` | Gris |
| vendidas | `estado=VENDIDA` | Azul |
| sin precio | `publicada=True, precio_venta_sugerido=0 o null` | Rojo (si > 0) |

**"Potencial restante":**
```
valor_potencial = SUM(precio_venta_sugerido)
    WHERE estado IN (DISPONIBLE, RESERVADA)
      AND activo=True
      AND precio_venta_sugerido > 0
```
Incluye piezas no publicadas (potencial de lo que puede generar si se publica todo).

**Si no hay piezas aún (etapa INGRESADO, 0 confirmadas):**
```
│  Sin piezas confirmadas aún.    │
│  [Revisar sugerencias →]        │
```

---

### 5.6 Bloque "Requiere atención"

Solo visible si hay al menos una alerta activa. Si no hay alertas, la zona desaparece (no se muestra "Sin alertas" — la ausencia de alertas no necesita declararse).

**Catálogo de alertas — con mensajes exactos:**

| Código | Condición | Mensaje visible |
|--------|-----------|----------------|
| `ALERTA_SIN_COSTO` | `costo_adquisicion IS NULL` | "Sin costo registrado — los KPIs de rentabilidad no están disponibles." |
| `ALERTA_SIN_PRECIO` | N piezas activas con precio=0 | "N piezas sin precio — no contribuyen al potencial de recuperación." |
| `ALERTA_ESTANCADO` | PUBLICADO > 30 días sin ventas | "XX días publicado sin ventas. Revisa si los precios son competitivos." |
| `ALERTA_SIN_PUBLICAR` | CONFIRMADO o EN_ALMACEN > 7 días | "Tiene piezas listas para publicar desde hace N días." |
| `ALERTA_RESERVA_VENCIDA` | ReservaDesarme vencida activa | "Hay una reserva vencida hace N horas. Libera o confirma la venta." |

Cada alerta tiene su botón de acción directo debajo del texto.

---

### 5.7 Barra de accesos rápidos

```
[Registrar venta]   [Publicar piezas]   [Ver en kiosko]   [Más acciones ▾]
```

**Reglas:**
- Máximo 3 acciones directas. El resto va en el menú "Más acciones".
- Las acciones visibles cambian según el estado del vehículo (tabla en §6).
- "Más acciones" incluye: Editar vehículo, Historial completo, Imprimir ficha, Cerrar vehículo.
- En CERRADO: la barra muestra solo "Ver historial" y "Exportar".

---

### 5.8 Feed de actividad (colapsado por defecto)

```
▾ Actividad reciente
  05 ago  —  Venta: Alternador → $85.000 (Documento #1047)
  03 ago  —  Precio actualizado: Capo → $45.000
  01 ago  —  3 piezas publicadas al kiosko
  28 jul  —  14 piezas confirmadas
  15 jul  —  Vehículo publicado
```

Colapsado por defecto en desktop. Expandible con un clic. En mobile no aparece en el scroll principal — está en una tab separada.

---

## 6. Comportamiento por etapa

### 6.1 INGRESADO

El vehículo acaba de entrar. Nadie sabe aún qué piezas tiene.

**Siguiente acción:**
```
El sistema sugiere 34 piezas para este vehículo.
Revisa cuáles están disponibles y cuáles descartar.

                              [Revisar piezas sugeridas →]
```

**KPIs:** Muestra "PAGASTE" si hay costo. Las demás tarjetas en $0 / gris.
**Piezas:** Ninguna confirmada todavía. Muestra "Sin piezas confirmadas. [Revisar sugerencias →]"
**Alertas:** Solo `ALERTA_SIN_COSTO` si aplica.
**Accesos rápidos:** [Revisar piezas] [Editar vehículo] [Más acciones ▾]

---

### 6.2 CONFIRMADO

El operador confirmó qué piezas tiene. Están registradas pero no desmontadas ni publicadas.

**Siguiente acción (caso normal):**
```
Tienes 23 piezas confirmadas con un potencial de $1.820.000.
Publícalas en el kiosko cuando estén listas para vender.

              [Ver piezas →]         [Publicar todas →]
```

**Siguiente acción (si llevan > 7 días sin publicar):**
```
Hay 23 piezas confirmadas esperando publicación desde hace 9 días.
Cuanto antes estén en el kiosko, antes empiezan a generar ingresos.

                              [Publicar piezas →]
```
Color del bloque: amarillo.

**KPIs:** Muestra potencial estimado. Ingresos = $0 (aún sin ventas).
**Alertas:** `ALERTA_SIN_PUBLICAR` si > 7 días, `ALERTA_SIN_PRECIO` si hay piezas sin precio.
**Accesos rápidos:** [Ver piezas] [Publicar piezas] [Más acciones ▾]

---

### 6.3 EN_ALMACEN

Las piezas están físicamente almacenadas pero aún no publicadas.

**Siguiente acción:**
```
Las piezas están guardadas y listas para el kiosko.
Publícalas para que los compradores puedan encontrarlas.

                              [Publicar piezas →]
```

**Diferencia con CONFIRMADO:** En esta etapa las piezas tienen ubicación física registrada. El botón "Publicar" está más habilitado — no hay bloqueo por etapa_fisica.

**KPIs:** Igual que CONFIRMADO.
**Alertas:** `ALERTA_SIN_PUBLICAR` con mayor urgencia si lleva más días.
**Accesos rápidos:** [Publicar piezas] [Ver inventario] [Más acciones ▾]

---

### 6.4 PUBLICADO

Las piezas están visibles en el kiosko. El operador espera consultas y ventas.

**Siguiente acción — variante A (recién publicado, < 7 días):**
```
23 piezas están publicadas en el kiosko. Espera las primeras consultas.

              [Ver en kiosko →]         [Compartir link →]
```
Color del bloque: verde.

**Siguiente acción — variante B (7–30 días sin ventas):**
```
Llevan N días publicadas sin ventas. Revisa si los precios están bien.

              [Revisar precios →]       [Ver en kiosko →]
```
Color del bloque: amarillo.

**Siguiente acción — variante C (> 30 días sin ventas):**
```
30 días sin ventas. Es probable que los precios estén por encima del mercado.
Reducir precios un 10–15% suele reactivar el interés.

              [Revisar precios →]       [Ver en kiosko →]
```
Color del bloque: rojo.

**Siguiente acción — variante D (hay ventas recientes, todo bien):**
```
Todo va bien. Última venta hace 3 días. Sigue gestionando consultas.

              [Registrar venta →]       [Ver inventario →]
```
Color del bloque: verde.

**KPIs:** Todas las 4 tarjetas activas (si hay costo registrado).
**Alertas:** `ALERTA_SIN_PRECIO`, `ALERTA_ESTANCADO`, `ALERTA_RESERVA_VENCIDA`.
**Accesos rápidos:** [Registrar venta] [Ver en kiosko] [Revisar precios] [Más acciones ▾]

---

### 6.5 VENDIENDO

El vehículo tiene ventas activas. Esta es la etapa de mayor actividad financiera.

**Siguiente acción:**
```
Recuperaste el 47% de lo que pagaste ($1.504.000 de $3.200.000).
Tienes 18 piezas activas en kiosko. Sigue registrando ventas.

              [Registrar venta →]       [Ver inventario →]
```
Color del bloque: verde.

**Si el ritmo cae (> 15 días sin ventas en VENDIENDO):**
```
Llevas 15 días sin registrar ventas. ¿Todo está bien?
Revisa si hay consultas pendientes o piezas que necesitan precio.

              [Ver consultas →]         [Revisar precios →]
```
Color del bloque: amarillo.

**KPIs:** Plena actividad. La barra de RECUPERASTE se actualiza en cada venta.
**Alertas:** `ALERTA_RESERVA_VENCIDA`, `ALERTA_SIN_PRECIO`.
**Accesos rápidos:** [Registrar venta] [Ver inventario] [Ver en kiosko] [Más acciones ▾]

---

### 6.6 CERRADO

El vehículo terminó su ciclo. La pantalla es de solo lectura — resumen final.

**Siguiente acción:**
```
Este vehículo está cerrado. Generó $2.840.000 en total.
Recuperaste el 88% de lo que pagaste.

              [Ver historial completo →]
```
Color del bloque: gris.

**KPIs:** Finales, no editables. Se agrega una quinta tarjeta: "QUEDÓ SIN VENDER" con el valor de piezas que fueron a SCRAP o FALTANTE.

**Piezas:** Muestra el desglose final (vendidas / scrap / faltante). No hay botones de acción.

**Alertas:** Ninguna. El vehículo está cerrado.

**Accesos rápidos:** [Ver historial] [Exportar ficha] [Reabrir vehículo ▾ (oculto, solo admin)]

---

## 7. Reglas de "Siguiente acción recomendada"

El sistema evalúa estas condiciones **en orden de prioridad** (la primera que se cumpla es la que se muestra):

```
1. ALERTA_RESERVA_VENCIDA activa
   → "Hay una reserva vencida. Libera o confirma la venta." [Revisar reserva →]
   Color: ROJO

2. PUBLICADO y > 30 días sin ventas
   → "30 días sin ventas. Revisa los precios." [Revisar precios →]
   Color: ROJO

3. PUBLICADO o EN_ALMACEN y ALERTA_SIN_PUBLICAR activa (> 7 días)
   → "Piezas esperando publicación N días." [Publicar →]
   Color: AMARILLO

4. PUBLICADO y 7–30 días sin ventas
   → "N días sin ventas. Revisa si los precios están bien." [Revisar precios →]
   Color: AMARILLO

5. INGRESADO
   → "Revisa las piezas sugeridas." [Revisar piezas →]
   Color: AZUL (informativo)

6. CONFIRMADO o EN_ALMACEN y piezas sin publicar
   → "Tienes piezas listas para publicar." [Publicar →]
   Color: AZUL

7. PUBLICADO o VENDIENDO y ventas recientes (< 7 días)
   → "Todo va bien. [Registrar venta →]"
   Color: VERDE

8. CERRADO
   → "Vehículo cerrado. [Ver historial →]"
   Color: GRIS
```

---

## 8. Comportamiento móvil

El operador no gestiona el Centro de Operaciones desde el celular en flujo normal — pero sí consulta. En mobile la pantalla se apila verticalmente en este orden de prioridad:

```
1.  Cabecera viva (vehículo + estado + días)
2.  [Tab: Resumen | Piezas | Actividad]
    Tab activo por defecto: Resumen
3.  En tab Resumen:
    a. Siguiente acción (full width, borde coloreado)
    b. KPIs en grid 2×2
    c. Alertas (si existen)
    d. Accesos rápidos (barra fija al fondo)
4.  En tab Piezas:
    a. Conteos (publicadas / en proceso / vendidas)
    b. Potencial restante
    c. Link a inventario
5.  En tab Actividad:
    a. Feed completo expandido
```

**Barra de acciones fija en mobile:**
```
╔════════════════════════════════════════╗
║  [+ Venta]  [Publicar]  [Kiosko]  [⋮] ║
╚════════════════════════════════════════╝
```

Los botones son grandes (mínimo 44px de altura). La barra se superpone al scroll.

**La barra de progreso en mobile:** colapsada a texto: "Etapa 4 de 5: PUBLICADO". Tap para expandir.

---

## 9. Estados vacíos y de borde

### 9.1 Vehículo recién creado (segundos después)

```
INGRESADO  ────  ...  ────  ...  ────  ...

┌─────────────────────────────────────────┐
│  ▶  SIGUIENTE ACCIÓN                    │
│     El sistema está preparando las      │
│     sugerencias de piezas para este     │
│     vehículo. Esto tarda unos segundos. │
│                                         │
│                  [Revisar cuando esté →]│
└─────────────────────────────────────────┘
```

### 9.2 Sin costo registrado

Las tarjetas 3 (RECUPERASTE) y 4 (AÚN FALTA) muestran:
```
┌────────────────┐  ┌──────────────┐
│  RECUPERASTE   │  │  AÚN FALTA   │
│      —         │  │      —       │
│  Sin costo     │  │  Sin costo   │
│  [Agregar →]  │  │  [Agregar →]│
└────────────────┘  └──────────────┘
```
No se muestra cero. No se muestra "N/A". Se muestra "—" con la acción para resolverlo.

### 9.3 Sin piezas con precio (todas en $0)

El potencial restante muestra:
```
│  Potencial restante:                │
│  Sin precios registrados            │
│  [Ver piezas sin precio →]         │
```

### 9.4 Vehículo cerrado con pérdida (ingresos < costo)

Las tarjetas muestran el resultado negativo de forma honesta:
```
┌────────────────┐
│  RECUPERASTE   │
│      62%       │
│  ██████░░░░░   │
│  Vendiste con  │
│  pérdida       │
└────────────────┘
```
Sin dramatismo extra. Solo el dato.

### 9.5 Vehículo con 0 piezas (SCRAP total)

```
│  PIEZAS                             │
│                                     │
│  0  publicadas                      │
│  0  en proceso                      │
│  0  vendidas                        │
│  0  a scrap                         │
│                                     │
│  Todos los materiales fueron a      │
│  reciclaje o declarados faltantes.  │
└─────────────────────────────────────┘
```

---

## 10. Experiencia del operador nuevo — primer ingreso

Cuando el operador abre por primera vez el Centro de Operaciones (post-onboarding), el sistema muestra un tooltip de orientación, no un tutorial completo:

```
┌──────────────────────────────────────────────────────────┐
│  Esta es la ficha de tu vehículo. Aquí verás todo lo     │
│  que necesitas saber y qué hacer a continuación.         │
│                                                           │
│  Empieza revisando las piezas sugeridas.                 │
│                                          [Entendido →]   │
└──────────────────────────────────────────────────────────┘
```

El tooltip apunta visualmente al bloque "Siguiente acción". Desaparece en el siguiente clic o si el operador ya visitó esta pantalla antes (flag en sesión).

**El operador nuevo no debería necesitar preguntar:**
- Qué hace este vehículo aquí
- Qué es el "potencial restante"
- Qué diferencia hay entre "publicadas" y "en proceso"
- Qué significa el porcentaje de recuperación

Si alguna de esas preguntas surge en tests con usuarios reales, el elemento correspondiente necesita rediseño antes de implementar P2.

---

## 11. Lo que esta pantalla NO hace

Estas restricciones son tan importantes como el diseño mismo:

- **No proyecta el futuro.** No dice "a este ritmo recuperarás el costo en 12 días". Solo describe el estado actual.
- **No tiene pestañas de navegación interna** (excepto en mobile donde es inevitable). Todo está visible en scroll.
- **No muestra gráficos de línea de tendencia.** Solo barras de progreso y conteos.
- **No tiene tabla de piezas completa.** El resumen de piezas es un conteo. Para ver el detalle existe el inventario.
- **No repite información entre zonas.** Si algo aparece en KPIs no aparece en Resumen de piezas.
- **No bloquea acciones según etapa** (eso es lógica de P2). La pantalla siempre muestra los botones disponibles; la lógica de transición valida en el servidor.
- **No envía notificaciones desde aquí.** Las alertas son visibles en la pantalla; no activan push ni email.

---

## 12. Componentes que P2 debe implementar

Para construir el Centro de Operaciones, P2 necesita lo siguiente (aquí solo se nombra; el cómo está en `desarmaduria_v2_plan_p0_p5.md`):

| Componente | Depende de |
|-----------|-----------|
| Campo `etapa` en VehiculoDesarme | Migración P2 |
| `get_vehicle_operations_summary(vehiculo)` | P2 — función de lectura, sin efectos |
| Lógica de "Siguiente acción" | P2 — evaluación de condiciones |
| Conteos de piezas por estado | P1 ya tiene `publicada`; P2 agrega `etapa_fisica` |
| Cálculo de alertas activas | P2 — evaluadas en la vista, no pre-computadas |
| Feed de actividad | P2 — modelo EventoVehiculo o similar |
| Template `centro_operaciones.html` | P2 |

---

## 13. Criterios de aceptación de diseño

Antes de implementar una sola línea de P2, validar este diseño con al menos un operador real (o alguien que conozca el flujo de una desarmaduria):

- [ ] El operador puede decir en < 5 segundos qué debería hacer con este vehículo ahora mismo
- [ ] El operador puede decir cuánto recuperó sin abrir ningún submenú
- [ ] El operador comprende la diferencia entre "publicadas" y "en proceso" sin explicación
- [ ] El operador sabe qué hace el botón "Publicar piezas" antes de presionarlo
- [ ] El operador no pregunta "¿qué es el potencial restante?"
- [ ] El operador puede resolver una reserva vencida en 2 clics desde esta pantalla
- [ ] En mobile, el operador encuentra la acción principal en < 3 segundos
- [ ] El operador nuevo no necesita leer documentación para empezar

Si algún criterio falla, ajustar el diseño aquí antes de pasar a código.

---

## 14. Decisiones abiertas (no bloquean P2, pero hay que cerrarlas antes)

| # | Pregunta | Opciones | Impacto |
|---|----------|----------|---------|
| D1 | ¿El feed de actividad usa un modelo propio (EventoVehiculo) o lee de las tablas existentes? | Modelo propio (más costoso pero extensible) / Query compuesta (más frágil) | P2 — modelo |
| D2 | ¿El "Siguiente acción" se evalúa en la vista o se pre-computa? | En la vista (más fresco, más lento) / Pre-computado (más rápido, staleness) | P2 — arquitectura |
| D3 | ¿Cómo se registra la fecha de cambio de etapa? | Campo `fecha_etapa_actual` / Tabla de historial de etapas | P2 — modelo |
| D4 | ¿"Compartir link" de la variante A de PUBLICADO abre un modal o copia el link? | Modal con QR / Copia directa al portapapeles | P2 — UX menor |

Las decisiones D1, D2 y D3 deben cerrarse antes de escribir la migración de P2.
