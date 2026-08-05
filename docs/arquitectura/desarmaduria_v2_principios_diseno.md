# eGarage — Principios de Diseño de Producto
**Fecha:** 2026-08-05  
**Alcance:** Módulo de Desarmaduria v2. Aplicables a todo el producto.  
**Audiencia:** Equipo de producto, diseño y desarrollo.

---

> Estos principios no son reglas de implementación técnica.  
> Son compromisos con la experiencia del operador que usan el sistema.  
> Toda decisión de producto, diseño o arquitectura debe poder justificarse en uno de estos puntos.

---

## 1. El sistema siempre muestra el siguiente paso

El operador nunca debería preguntarse "¿y ahora qué hago?". Cada pantalla termina con una indicación clara de la acción que corresponde según el estado actual del negocio.

Si el sistema no puede determinar el siguiente paso, dice por qué y qué información falta para determinarlo.

---

## 2. El operador trabaja por excepción

El sistema no muestra todo lo que está bien. Solo llama la atención sobre lo que requiere acción. Si no hay alertas, no se muestra la sección de alertas. Si no hay retrasos, no se menciona el tiempo.

La ausencia de problemas no necesita ser declarada.

---

## 3. Una pantalla responde una pregunta principal

Cada pantalla tiene una pregunta que responde mejor que ninguna otra:

- La ficha del vehículo responde: "¿Cómo va este vehículo?"
- El dashboard responde: "¿Cómo va mi negocio esta semana?"
- El inventario responde: "¿Qué tengo disponible para vender?"

Las pantallas no compiten entre sí. No duplican información.

---

## 4. Toda estadística termina en una acción

Un número sin acción es decoración. Cada KPI visible en el sistema responde la pregunta "¿y entonces qué hago?", ya sea confirmando que todo está bien o sugiriendo un paso concreto.

**Mal:** "ROI: 87%"  
**Bien:** "Recuperaste el 87%. Te faltan $390.000 para cubrir la inversión. [Ver piezas disponibles →]"

---

## 5. El vehículo es el centro del sistema

La unidad de trabajo no es una pieza, ni una venta, ni un documento. Es el vehículo. Las piezas nacen del vehículo. Las ventas son consecuencia de las piezas. Los documentos son el registro de esas ventas.

El ciclo completo — desde que el vehículo entra al patio hasta que genera su última utilidad — es lo que el sistema administra.

---

## 6. Los repuestos, documentos y ventas nacen del ciclo del vehículo

eGarage no administra repuestos. Administra la vida completa de un vehículo.

Un repuesto existe porque un vehículo fue comprado. Un documento existe porque un cliente quiso ese repuesto. Una venta existe porque el operador gestionó ese ciclo completo.

El vehículo es el origen de todo lo demás en el módulo de desarmaduria.

---

## 7. El sistema usa lenguaje del negocio, no lenguaje de base de datos

Los operadores de desarmaduria no saben qué es un EBITDA, un margen bruto ni una tasa de rotación. Sí saben si compraron un Hilux en $3.000.000 y quieren saber si lo van a recuperar.

El sistema habla el idioma del operador, no el del contador ni el del programador.

| No usar | Usar |
|---------|------|
| "Margen bruto" | "Lo que te quedó" |
| "Tasa de rotación" | "Cuántas piezas vendiste este mes" |
| "ARPU" | "Promedio de venta por vehículo" |
| "Estado: PUBLICADO" | "Publicado en kiosko desde el 15 jul" |

---

## 8. Las acciones críticas son explícitas y reversibles cuando corresponda

El sistema no ejecuta acciones irreversibles sin confirmación explícita del operador. Cuando una acción no puede deshacerse (cerrar un vehículo, descartar piezas), el sistema lo dice antes de ejecutar.

Cuando una acción puede deshacerse (despublicar una pieza, reabrir una reserva), el sistema muestra cómo hacerlo.

---

## 9. El trabajo parcial es válido

Un vehículo puede estar parcialmente revisado. Una publicación puede tener solo algunas piezas. Un cierre puede estar en proceso.

El sistema no obliga a completar todo para poder usar algo. Permite el trabajo incremental y muestra el progreso en tiempo real.

---

## 10. La simplicidad visible no debe romper la integridad del backend

Lo que el operador ve es simple. Lo que ocurre en el servidor es correcto.

La complejidad del backend — bloqueos transaccionales, aislamiento multi-tenant, idempotencia, auditoría de eventos — es invisible para el usuario pero indispensable para la integridad del negocio.

Simplificar la interfaz nunca es excusa para sacrificar la integridad de los datos.
