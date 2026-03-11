# Fase B y C – Desarme: Seed y flujo operativo

Guía para ejecutar y revisar seed + flujo. **Fase A aprobada** (modelos, migraciones 0083–0088, constraint patente).

---

## B1. Mini-prueba constraint (validación obligatoria)

Confirmar que 0088 no solo está aplicada, sino funcional en runtime:

1. **Crear 2 vehículos** con `tipo_uso=desarme`, **misma empresa**, **patente="" o null**.
2. **Ambos deben guardar sin error.** Si pasa, la constraint permite múltiples vehículos sin patente por empresa.

Luego: seed → flujo operativo.

---

## B2. Seed

### 1. Ejecutar seed

```bash
python manage.py seed_plantillas_desarme
```

Salida esperada tipo: `Plantillas de desarme creadas: 5 (nuevas: 5)` (o “nuevas: 0” si ya existían).

### 2. Tres comprobaciones (no solo “que existan”)

- **Visibilidad a tenants:** las plantillas globales deben **aparecer realmente** en las vistas del tenant (listado desarme), no solo en admin.
- **Sin duplicados en re-ejecución:** volver a ejecutar el comando no debe duplicar plantillas globales (comportamiento idempotente).
- **Conteo de piezas consistente** por plantilla (tabla abajo). Revisar en detalle de cada plantilla que `zona_mapa`, `vista_mapa`, `lado` sean coherentes.

### 3. Cantidad de piezas por plantilla

Según el comando actual:

| Plantilla  | Piezas (aprox.) |
|-----------|------------------|
| Sedan     | 22               |
| SUV       | 18               |
| Pickup    | 15               |
| Hatchback | 18               |
| Manual    | 0                |

Comprobar en detalle de cada plantilla que el número de piezas coincida y que tengan (donde aplique) `zona_mapa`, `vista_mapa`, `lado` coherentes.

---

## C1. Flujo operativo real

Orden exacto (cadena completa de negocio, no pantallas aisladas):

| Paso | Acción | Qué revisar |
|-----|--------|-------------|
| 1 | **Crear vehículo de desarme** | tipo_uso=desarme, patente opcional; que guarde y quede en lista. |
| 2 | **Aplicar plantilla** | Desde el vehículo, elegir una plantilla (ej. Sedan) y aplicar; que se creen los repuestos asociados al vehículo. |
| 3 | **Abrir mapa** | Ir al mapa de piezas del vehículo (`taller:desarme:mapa_piezas` con `pk` del vehículo). Que cargue sin error. |
| 4 | **Editar 2–3 piezas** | Cambiar estado, precio, observaciones desde el mapa/drawer; guardado AJAX. Revisar que **lado** y **observaciones** se persistan y se muestren bien después (mapeos lado_pieza↔lado, observacion_estado↔observaciones). |
| 5 | **Revisar dashboard** | Entrar al dashboard financiero del vehículo (`taller:desarme:dashboard_financiero`). Que se vean costos/KPIs coherentes con el vehículo. |
| 6 | **Cerrar vehículo** | Usar la acción de cierre (`taller:desarme:cerrar_vehiculo`). Que estado pase a “cerrado” y activo_operacional a False. |

### Rutas de referencia (namespace `taller:desarme:`)

- Listado plantillas: `plantilla_list`
- Detalle plantilla: `plantilla_detail` (pk)
- Aplicar plantilla: `aplicar_plantilla` (pk del vehículo)
- Mapa de piezas: `mapa_piezas` (pk del vehículo)
- Dashboard: `dashboard_financiero` (pk del vehículo)
- Cerrar vehículo: `cerrar_vehiculo` (pk del vehículo)

(En la app las rutas están bajo `app_name = "desarme"`; la URL concreta depende de cómo se incluya en el proyecto, ej. `taller:desarme:...`.)

---

## Qué validar en cada paso

### Al aplicar plantilla

- Cada repuesto creado:
  - queda asociado a **vehiculo_origen** (el vehículo actual).
  - recibe **zona_mapa**, **vista_mapa** (y **lado** si aplica) desde la plantilla.
  - nace con un **estado válido** (ej. disponible).

### En edición AJAX del mapa

- Al guardar una pieza:
  - respuesta **200**.
  - cambios **persisten en BD**.
  - **recargar página** muestra el valor actualizado.
  - sin desalineación entre nombre en frontend y nombre en modelo:
    - frontend envía **observacion_estado** → backend guarda en **observaciones** → al leer de nuevo se muestra lo guardado.

### En dashboard

- Coherencia (más que diseño):
  - costos del vehículo visibles.
  - repuestos asociados reflejados.
  - KPIs no vacíos cuando sí hay datos.
  - sin mezclar datos de otras empresas (tenant).

### Al cerrar vehículo

- **estado_desarme** = `cerrado`.
- **activo_operacional** = `False`.
- El vehículo ya no debe aparecer como operativo en flujos activos (si así está diseñado).

---

## Riesgos más probables en B/C (no bloqueadores)

Fallos típicos de integración backend ↔ AJAX ↔ UI a tener en cuenta:

| Riesgo | Dónde mirar |
|--------|--------------|
| Plantilla visible en admin pero no en vistas tenant | Queryset de plantillas: debe incluir `empresa=None` para globales. |
| Seed crea globales pero listado no las muestra | Mismo: filtro por empresa/tenant. |
| Mapa carga pero drawer no persiste **lado** | Payload AJAX y campo en serializer/cleaned_data. |
| AJAX guarda **observacion_estado** pero al recargar no aparece | Template/API lee otro nombre; revisar serialización y render. |
| Cierre cambia estado pero no desactiva **activo_operacional** | Vista/command de cierre debe setear ambos. |
| Dashboard mezcla datos de otra empresa | Filtros por empresa en consultas y contexto. |

---

## Puntos a vigilar (naming, no ausencia de datos)

- **lado_pieza ↔ lado:** aplicación de plantilla, mapa/drawer; que “lado” se guarde y se muestre bien.
- **observacion_estado ↔ observaciones:** edición de pieza (AJAX), lectura posterior; que se persista en `observaciones` y se muestre correctamente.

---

## Criterio de salida: B/C aprobadas cuando

| Condición | |
|-----------|---|
| Mini-prueba de patente vacía | OK |
| Seed idempotente | OK |
| Plantillas globales visibles en tenant | OK |
| Aplicar plantilla crea repuestos con datos de mapa/lado | OK |
| Edición AJAX persiste y re-renderiza | OK |
| Dashboard no mezcla empresa y muestra datos coherentes | OK |
| Cierre cambia estado_desarme y activo_operacional | OK |

Si falla algo de ahí → **incidencia puntual de integración B/C** (no reapertura de Fase A).

---

## Registro de resultado (ejecutar B1 → B2 → C1 en ese orden)

Rellenar breve por paso para clasificar rápido: bloqueante / bug menor / ajuste UI / listo para Fase D.

```
B1. Mini-prueba patente vacía:     OK / Falla — evidencia: ___
B2. Seed:                          OK / Falla — evidencia: ___
C1.1 Crear vehículo desarme:       OK / Falla
C1.2 Aplicar plantilla:            OK / Falla
C1.3 Abrir mapa:                   OK / Falla
C1.4 Editar piezas (AJAX):          OK / Falla
C1.5 Dashboard:                    OK / Falla
C1.6 Cerrar vehículo:              OK / Falla
```

---

## Después de B/C

Con el resultado anterior (mini-prueba + seed + flujo con 1 vehículo de prueba):

- Incidencias = **integración/UI**; no reabrir Fase A.
- Revisar juntos y clasificar: **bloqueante real** / **bug menor** / **ajuste UI** / **listo para Fase D**.
- Decidir si abrir **Fase D** (tenant, permisos, KPIs, rutas, UX) con diagnóstico preciso.
