# Auditoría del visor visual y viabilidad de sedán 3D para desarmaduría

Fecha de auditoría: 2026-10-15  
Alcance: inspección estática del repositorio. No se implementaron cambios funcionales.

## Resumen ejecutivo

El sistema ya tiene un **mapa visual 2D interactivo**, presentado en la interfaz como “Gemelo digital”, para vehículos de desarme. Está compuesto por siluetas SVG inline, zonas seleccionables (`visual_slot`), una API JSON de inventario, colores derivados del estado/ubicación/origen y un panel lateral con acciones. El sedán existente es un wireframe SVG lateral; **no es un visor 3D**.

No se encontró infraestructura 3D: no hay Three.js, WebGL, `<model-viewer>`, cámara orbital, escena, luces, raycasting, archivos GLB/GLTF/OBJ ni un modelo tridimensional de sedán. Por tanto, el sedán 3D interactivo todavía requiere tanto el activo 3D como su runtime, mapeo anatómico y estrategia de integración.

Las referencias pedidas tampoco son código 3D:

- `taller/desarme/views.py:1995` inicia `_revisar_finalizar_sesion`, una operación transaccional de cierre de sesión de despiece que materializa sugerencias confirmadas como inventario.
- `taller/tests/test_p3_sesion_visual.py:232` inicia una prueba backend que confirma que dicha operación crea tres `PiezaDesarme` en bulk. “visual” forma parte del nombre histórico del archivo de pruebas, no convierte esa prueba en una validación de visor 3D.

## Hallazgos comprobados

### 1. Catálogo predeterminado efectivo

La selección depende del país de la empresa:

- Empresa con `pais == "US"`: catálogo USA de 115 ítems, definido en `taller/catalogos/catalogo_piezas_desarme_usa.py`.
- Cualquier otra empresa, incluyendo CL/MX: catálogo legacy de 107 ítems, definido en `taller/desarme/catalogo_piezas.py`.

`get_catalogo_operativo_desarme()` normaliza ambos a `{codigo, nombre, zona, precio_base}`. Luego `get_catalogo_para_vehiculo()` aplica exclusiones por carrocería y finalmente la configuración de la empresa (`CatalogoRepuestoEmpresa`), que puede excluir códigos o reemplazar precios. Es decir, las listas siguientes son el **predeterminado de código**, no necesariamente la lista final de una empresa ya configurada.

#### Catálogo legacy (107 ítems; precios base CLP 2026)

##### Motor (13)

- MOT-01 Alternador — $95.000
- MOT-02 Arranque — $80.000
- MOT-03 Motor completo — $850.000
- MOT-04 Bloque motor — $250.000
- MOT-05 Tapa de cilindros — $110.000
- MOT-06 Distribuidor — $38.000
- MOT-07 Bomba de agua — $48.000
- MOT-08 Radiador — $72.000
- MOT-09 Ventilador radiador — $28.000
- MOT-10 Múltiple admisión — $60.000
- MOT-11 Múltiple escape — $52.000
- MOT-14 Bomba inyectora — $90.000
- MOT-15 Inyectores (set) — $100.000

##### Carrocería (17)

- CAR-01 Capot — $90.000
- CAR-02 Puerta delantera izq — $82.000
- CAR-03 Puerta delantera der — $82.000
- CAR-04 Puerta trasera izq — $72.000
- CAR-05 Puerta trasera der — $72.000
- CAR-06 Baguetera — $100.000
- CAR-07 Tapa baúl — $62.000
- CAR-08 Parachoques delantero — $52.000
- CAR-09 Parachoques trasero — $48.000
- CAR-10 Guardabarros izq — $42.000
- CAR-11 Guardabarros der — $42.000
- CAR-12 Puerta maletero — $48.000
- CAR-13 Tapa de bencinera — $20.000
- CAR-14 Espejo lateral izq — $48.000
- CAR-15 Espejo lateral der — $48.000
- CAR-16 Vidrio parabrisas — $120.000
- CAR-17 Vidrio luneta trasera — $90.000

##### Interior (14)

- INT-01 Asiento delantero izq — $80.000
- INT-02 Asiento delantero der — $80.000
- INT-03 Asiento trasero — $60.000
- INT-04 Tablero completo — $135.000
- INT-05 Volante — $38.000
- INT-06 Palanca de cambios — $28.000
- INT-07 Consola central — $32.000
- INT-08 Alfombra delantera — $18.000
- INT-09 Alfombra trasera — $15.000
- INT-10 Airbag conductor — $90.000
- INT-11 Airbag pasajero — $90.000
- INT-12 Retrovisor interior — $15.000
- INT-13 Tapacubos volante — $10.000
- INT-14 Cinturones de seguridad (set) — $42.000

##### Suspensión (15)

- SUS-01 Amortiguador delantero izq — $48.000
- SUS-02 Amortiguador delantero der — $48.000
- SUS-03 Amortiguador trasero izq — $40.000
- SUS-04 Amortiguador trasero der — $40.000
- SUS-05 Resorte delantero (par) — $28.000
- SUS-06 Resorte trasero (par) — $25.000
- SUS-07 Brazo inferior izq — $60.000
- SUS-08 Brazo inferior der — $60.000
- SUS-09 Rótula dirección izq — $28.000
- SUS-10 Rótula dirección der — $28.000
- SUS-11 Maza delantera izq — $48.000
- SUS-12 Maza delantera der — $48.000
- SUS-13 Dirección hidráulica — $90.000
- SUS-14 Barra estabilizadora — $38.000
- SUS-15 Cremallera — $65.000

##### Iluminación (12)

- ILU-01 Óptico delantero izq — $120.000
- ILU-02 Óptico delantero der — $120.000
- ILU-03 Óptico trasero izq — $55.000
- ILU-04 Óptico trasero der — $55.000
- ILU-05 Luz de neblina izq — $30.000
- ILU-06 Luz de neblina der — $30.000
- ILU-07 Luz de techo — $12.000
- ILU-08 Intermitente delantero izq — $18.000
- ILU-09 Intermitente delantero der — $18.000
- ILU-10 Luz de placa — $8.000
- ILU-11 Tercer stop — $18.000
- ILU-12 Luz diurna (DRL) izq — $28.000

##### Electrónica (18)

- ELE-01 Radio / pantalla multimedia — $68.000
- ELE-02 ECU / computadora motor — $115.000
- ELE-03 Batería — $50.000
- ELE-04 Sensores ABS (set) — $38.000
- ELE-05 Vidrio puerta del. izq — $30.000
- ELE-06 Vidrio puerta del. der — $30.000
- ELE-07 Vidrio puerta tras. izq — $24.000
- ELE-08 Vidrio puerta tras. der — $24.000
- ELE-09 Motor elevavidrios izq — $28.000
- ELE-10 Motor elevavidrios der — $28.000
- ELE-11 Sensores SRS — $48.000
- ELE-12 Fusibles y relay (set) — $15.000
- ELE-13 Cableado principal — $70.000
- ELE-14 Bomba combustible — $60.000
- ELE-15 Estarter — $48.000
- ELE-16 Módulo airbag (SRS) — $78.000
- ELE-17 Sensor parqueo trasero (set) — $22.000
- ELE-18 Cámara de retroceso — $35.000

##### Escape (8)

- ESC-01 Catalizador — $180.000
- ESC-02 Sonda lambda — $38.000
- ESC-03 Mofle central — $48.000
- ESC-04 Mofle trasero — $42.000
- ESC-05 Caño escape completo — $100.000
- ESC-06 Flexible escape — $28.000
- ESC-07 Soporte escape — $14.000
- ESC-08 Tapón escape — $8.000

##### Ruedas (10)

- RUE-01 Rueda 15" (con neumático) — $65.000
- RUE-02 Rueda 16" (con neumático) — $78.000
- RUE-03 Rueda 17" (con neumático) — $90.000
- RUE-04 Disco freno delantero (par) — $70.000
- RUE-05 Disco freno trasero (par) — $60.000
- RUE-06 Tambor freno trasero (par) — $50.000
- RUE-07 Pinza freno delantera izq — $82.000
- RUE-08 Pinza freno delantera der — $82.000
- RUE-09 Pastillas freno (set) — $38.000
- RUE-10 Tambor (unidad) — $28.000

Hay además dos piezas opcionales que **no se incorporan al catálogo base**: OPC-01 Turbo ($200.000) y OPC-02 Intercooler ($90.000).

#### Catálogo USA (115 ítems)

El adaptador usa el nombre oficial inglés y asigna un precio de referencia por zona, no por ítem: Motor USD 250; Transmisión USD 350; Suspensión USD 80; Frenos USD 60; Cooling USD 50; Electrónica USD 40; Carrocería USD 70.

- **Motor (23):** `engine_assembly`, `engine_block`, `cylinder_head`, `camshaft`, `crankshaft`, `piston`, `valve_cover`, `oil_pan`, `intake_manifold`, `exhaust_manifold`, `distributor`, `turbocharger`, `intercooler`, `injection_pump`, `fuel_injector_set`, `catalytic_converter`, `oxygen_sensor`, `center_muffler`, `rear_muffler`, `exhaust_pipe_complete`, `flex_exhaust_pipe`, `exhaust_hanger`, `exhaust_end_cap`.
- **Transmisión (5):** `transmission_auto`, `transmission_manual`, `torque_converter`, `driveshaft`, `rear_differential`.
- **Suspensión (20):** `front_shock`, `rear_shock`, `strut_assembly`, `control_arm`, `sway_bar`, `sway_bar_link`, `front_shock_left`, `front_shock_right`, `rear_shock_left`, `rear_shock_right`, `front_spring_pair`, `rear_spring_pair`, `lower_control_arm_left`, `lower_control_arm_right`, `tie_rod_end_left`, `tie_rod_end_right`, `front_hub_left`, `front_hub_right`, `power_steering_pump`, `steering_rack`.
- **Frenos (14):** `brake_rotor`, `brake_caliper`, `brake_master_cylinder`, `brake_booster`, `wheel_15`, `wheel_16`, `wheel_17`, `front_brake_disc_pair`, `rear_brake_disc_pair`, `rear_brake_drum_pair`, `front_brake_caliper_left`, `front_brake_caliper_right`, `brake_pads_set`, `brake_drum_unit`.
- **Cooling (3):** `radiator`, `radiator_fan`, `water_pump`.
- **Electrónica (18):** `alternator`, `starter_motor`, `ecu`, `battery`, `radio_unit`, `ecu_computer`, `abs_sensor_set`, `front_window_left`, `front_window_right`, `rear_window_left`, `rear_window_right`, `window_regulator_motor_left`, `window_regulator_motor_right`, `srs_sensor_set`, `fuse_relay_set`, `main_wiring_harness`, `fuel_pump`, `starter`.
- **Carrocería (32):** `front_bumper_cover`, `rear_bumper_cover`, `hood`, `fender`, `door`, `trunk_lid`, `liftgate`, `side_mirror`, `steering_wheel`, `dashboard`, `center_console`, `seat`, `airbag`, `fuel_filler_door`, `gear_shifter`, `front_floor_mat`, `rear_floor_mat`, `rear_view_mirror_inner`, `steering_wheel_hub_cap`, `seat_belt_set`, `headlight_left`, `headlight_right`, `tail_light_left`, `tail_light_right`, `fog_light_left`, `fog_light_right`, `dome_light`, `turn_signal_left`, `turn_signal_right`, `license_plate_light`, `rear_lamp_left`, `rear_lamp_right`.

#### Variación por carrocería

Para un sedán, el catálogo legacy excluye únicamente CAR-12 “Puerta maletero”, porque mantiene CAR-07 “Tapa baúl”: queda en 106 sugerencias antes de configuración de empresa. Otras carrocerías tienen exclusiones propias; motos usan una whitelist. Tipo nulo, vacío o desconocido conserva el catálogo completo.

### 2. Estados existentes

No existe un único estado global; hay capas diferentes y no deben confundirse:

| Entidad/capa | Estados comprobados | Propósito |
|---|---|---|
| `VehiculoDesarme.estado_operativo` | INGRESADO, EN_REVISION, EN_PROCESAMIENTO, EN_CIERRE, CERRADO | Ciclo operacional canónico del vehículo |
| `VehiculoDesarme.estado_desarme` (legacy) | INGRESADO, DESARMANDO, DESARMADO, AGOTADO, RECUPERADO, CERRADO, BAJA | Estado histórico, declarado independiente del operacional |
| `SugerenciaPiezaDesarme.estado` | PENDIENTE, CONFIRMADA, DESCARTADA | Progreso de revisión previa a crear inventario |
| Estado visual de sugerencia | gris, verde, amarillo, rojo | gris=PENDIENTE; verde=CONFIRMADA buena/excelente/nueva; amarillo=CONFIRMADA regular; rojo=DESCARTADA |
| `PiezaDesarme.estado_pieza` | DISPONIBLE, RESERVADA, VENDIDA, DANADA, SCRAP, FALTANTE | Estado comercial/físico de la partida |
| `PiezaDesarme.condicion` | NUEVO, EXCELENTE, BUENA, REGULAR | Condición física |
| `PiezaDesarme.ubicacion_tipo` | VEHICULO, BODEGA, TRANSITO, TERCERO | Dónde está la pieza |
| `PiezaDesarme.origen` | DESARME_PROPIO, COMPRA_EXTERNA, LOTE_YARDA, RECOMPRA | Procedencia |
| Publicación/actividad | `publicada` y `activo` booleanos | Visibilidad en kiosko/storefront y vigencia |

El mapa visual traduce estas dimensiones a clases dominantes: no disponible para DANADA/FALTANTE/SCRAP; externa si no es DESARME_PROPIO; vendida; bodega; o montada. Si varias piezas comparten slot, prioriza no disponible > externa > vendida > bodega > montada.

### 3. Relación de los repuestos con cada vehículo

El modelo raíz es `VehiculoDesarme`, separado del `Vehiculo` de reparación. Todas las entidades están aisladas por `empresa` mediante `TenantScoped`.

1. `inicializar_sugerencias(vehiculo, empresa)` obtiene el catálogo efectivo para ese vehículo y crea una `SugerenciaPiezaDesarme` PENDIENTE por código mediante `get_or_create`.
2. Cada sugerencia guarda un snapshot de código, nombre, zona y precio. La restricción única `(vehiculo_desarme, codigo)` impide repetir el mismo código dentro del vehículo.
3. La revisión cambia la sugerencia a CONFIRMADA o DESCARTADA y puede establecer condición/precio.
4. Al finalizar, cada sugerencia CONFIRMADA aún sin `pieza_creada` produce una `PiezaDesarme`.
5. `PiezaDesarme.vehiculo_desarme` es FK obligatoria con `PROTECT` y `related_name="piezas_desarme"`: toda pieza física queda asociada a un vehículo y un vehículo con piezas protegidas no puede borrarse accidentalmente.
6. `SugerenciaPiezaDesarme.pieza_creada` enlaza la sugerencia original con la pieza materializada; es nullable y usa `SET_NULL`.
7. `PiezaDesarme.visual_slot` es un string anatómico opcional. Solo las piezas que tengan un valor idéntico a un `data-visual-slot` del SVG aparecen vinculadas/iluminadas en el mapa.
8. El endpoint del mapa incluye piezas propias del vehículo y, cuando hay coincidencias por marca/modelo/año, piezas externas compatibles determinadas por `PartApplication` o `InterchangePieza` y códigos compatibles.

No hay una tabla canónica que relacione cada código de catálogo con un slot visual. El catálogo usa códigos/zonas, mientras el mapa usa cadenas como `engine.core`, `door.front.left` o `wheels`; la unión depende del campo manual `visual_slot` de cada `PiezaDesarme`.

### 4. Qué hace exactamente `taller/desarme/views.py:1995`

La línea 1995 declara `_revisar_finalizar_sesion(data, vehiculo, empresa, user, request)`. Su comportamiento comprobado es:

- Abre `transaction.atomic()`.
- Busca y bloquea (`select_for_update`) sugerencias de esa empresa y vehículo con estado CONFIRMADA y `pieza_creada IS NULL`.
- Si no hay ninguna, responde HTTP 400 y no crea inventario.
- Construye una `PiezaDesarme` por sugerencia y ejecuta `bulk_create`.
- Copia código, nombre, zona, precio sugerido y condición; fija `estado_pieza=DISPONIBLE`, `activo=True`, `revisado=True`, fecha de revisión actual y cantidad 1.
- Enlaza cada sugerencia con su pieza recién creada.
- Registra `VehiculoDesarmeEvent` de tipo `SESION_DESPIECE_FINALIZADA`, con cantidad creada y usuario.
- Actualiza el vehículo a `estado_operativo=EN_PROCESAMIENTO`.
- Devuelve JSON con éxito, cantidad y URL de redirección.

No carga gráficos, no entrega geometría, no asigna `visual_slot`, no opera una cámara ni renderiza 3D. Es lógica transaccional de persistencia y avance de workflow.

### 5. Qué hace exactamente `taller/tests/test_p3_sesion_visual.py:232`

La línea 232 declara `test_finalizar_crea_piezas_en_bulk`. La prueba:

- crea tres sugerencias CONFIRMADAS de prueba asociadas al mismo vehículo;
- hace POST con `action="finalizar_sesion"` al endpoint de revisión;
- exige `success == true`;
- exige `piezas_creadas == 3`;
- comprueba que existen exactamente tres `PiezaDesarme` de esa empresa y vehículo.

Es una prueba de integración del cierre de sesión y creación de inventario. No inspecciona HTML, SVG, canvas, WebGL, slots, interacción visual ni modelo 3D. El archivo también prueba agrupación y tokens visuales de la sesión, pero esta prueba concreta no valida un visor.

### 6. Infraestructura visual que ya existe

- `templates/taller/desarme/partials/_vehiculo_mapa_visual.html`: contenedor del “Gemelo digital”, leyenda, viewport, selección de silueta por carrocería y drawer.
- Wireframes SVG inline para sedán, SUV, pickup, coupé y van en `templates/taller/desarme/partials/vehicles/`.
- El sedán tiene 11 grupos seleccionables: `engine.core`, `transmission`, cuatro puertas, `body.bed`, `body.rear.tailgate`, suspensión delantera/trasera y `wheels`.
- `templates/taller/desarme/ver_vehiculo.html`: estilos y JavaScript actualmente usados. Consulta la API, agrupa por `visual_slot`, pinta estados, permite mouse/teclado, abre el detalle y enlaza editar/cambiar estado/vender.
- `api_mapa_piezas_vehiculo`: API tenant-scoped con vehículo, resumen y piezas compactas; expone estado, ubicación, origen, slot y precio.
- Campos de soporte: `VehiculoDesarme.tipo_carroceria`, `numero_puertas`, `ubicacion_fisica`; y `PiezaDesarme.visual_slot`, estado, ubicación y origen.
- Pruebas específicas en `taller/tests/test_desarme_mapa_visual_api.py` cubren formulario, aislamiento tenant, payload y compatibilidad externa.
- Existe `static/taller/desarme/svg/sedan_lateral.svg`, pero no se encontró referencia activa desde plantillas/código.
- Existen `static/js/desarme/vehicle-map.js`, `piece-drawer.js` y `static/taller/desarme/vehicle-map.css`, con una arquitectura visual anterior basada en clases `.zone`/vistas. No se encontraron referencias activas a esos archivos; la pantalla vigente implementa su lógica inline en `ver_vehiculo.html` y usa `.interactive-slot`. Deben considerarse activos potencialmente obsoletos, no infraestructura confirmada en ejecución.

### 7. Limitaciones comprobadas del mapa actual

- Es SVG 2D lateral, aunque la interfaz lo denomine “Gemelo digital”.
- No hay profundidad, rotación, zoom orbital, ocultación de capas ni selección por raycasting.
- La geometría es genérica y no depende de marca/modelo/año.
- La clase `doors-N` se emite, pero los grupos SVG del sedán incluyen siempre cuatro puertas; no se comprobó que esa clase cambie realmente la geometría.
- Los slots son muy gruesos frente a los 106 repuestos predeterminados de un sedán; muchos repuestos no tienen región propia.
- El sedán reutiliza nombres semánticos discutibles (`body.bed` y `body.rear.tailgate`), más propios de pickup/hatchback que de tapa de baúl de sedán.
- Las sugerencias del catálogo no reciben `visual_slot` al inicializarse ni al finalizar la sesión; las piezas creadas por `_revisar_finalizar_sesion` quedan con slot nulo salvo edición posterior.
- El mensaje vacío confirma este diseño: las piezas sin slot no se muestran en el mapa.
- La API soporta compatibles externos, pero los pinta únicamente si también tienen `visual_slot` coincidente.

## Pendientes para un sedán 3D interactivo

Los siguientes puntos son pendientes de producto/arquitectura; no se encontraron implementados:

1. **Definir alcance del 3D.** Decidir si será una vista estética, un selector anatómico, un explotado de componentes o los tres; y qué dispositivos/rendimiento/accesibilidad se deben soportar.
2. **Activo 3D del sedán.** Crear o licenciar un GLB/GLTF optimizado, con mallas separadas y nombres estables, materiales, pivotes, LOD y derechos de uso. No existe actualmente.
3. **Motor de render.** Elegir e integrar Three.js, Babylon.js o `<model-viewer>` según el nivel de interacción. Se requieren escena, cámara, controles, luces, carga, estados de error y fallback 2D.
4. **Taxonomía canónica de slots.** Diseñar IDs anatómicos suficientes para catálogo legacy y USA, con lateralidad y jerarquía. La taxonomía debe ser compartida entre catálogo, piezas físicas, SVG 2D y nodos/mallas 3D.
5. **Mapeo catálogo → slot.** Incorporar una fuente de datos explícita y versionada. Hoy no hay mapping automático y `visual_slot` se completa por pieza.
6. **Resolver granularidad.** Determinar cómo representar múltiples repuestos internos en una misma zona y varios registros por slot, incluyendo motor, interior, iluminación, electrónica, escape y frenos.
7. **Corregir semántica del sedán.** Reemplazar `body.bed`/`body.rear.tailgate` por slots adecuados (por ejemplo, maletero/tapa de baúl) y decidir el tratamiento de 2/4 puertas.
8. **Estados visuales 3D.** Especificar precedencia, colores, materiales, selección, piezas ausentes/vendidas/externas y combinaciones múltiples sin depender solo del color.
9. **API/contrato.** La API actual puede ser una base, pero necesita un contrato versionado de nodos 3D, disponibilidad, etiquetas, agrupación y quizá URLs/metadata del modelo.
10. **Interacción y accesibilidad.** Raycasting, foco por teclado, árbol/lista alternativo, tooltips, drawer, etiquetas ARIA, reducción de movimiento y navegación móvil.
11. **Rendimiento y despliegue.** Presupuesto de polígonos/texturas, compresión Draco/Meshopt/KTX2, caché/CDN, lazy loading, pruebas en móviles de gama media y fallback cuando WebGL no esté disponible.
12. **Pruebas.** Unitarias del mapping, contrato de API, pruebas de interacción, visual regression, carga/fallo del asset, aislamiento tenant y E2E que distinga explícitamente 2D de 3D.
13. **Migración/backfill.** Definir cómo asignar slots a piezas ya existentes y a nuevas piezas creadas en bulk. Sin esto, un visor 3D podría cargar correctamente pero verse vacío.
14. **Limpieza técnica planificada.** Confirmar si los assets visuales estáticos antiguos se retiran o reutilizan y mover, si corresponde, el CSS/JS inline vigente a módulos únicos para evitar dos implementaciones divergentes.

## Separación final: comprobado vs. no comprobado

### Comprobado

- Hay catálogo predeterminado dual: 107 piezas legacy y 115 USA.
- El catálogo se filtra por carrocería y configuración de empresa.
- Para sedán legacy se excluye CAR-12 y permanecen 106 ítems antes de personalización.
- Las sugerencias y piezas pertenecen a un vehículo de desarme y a una empresa.
- Hay estados diferenciados de vehículo, sugerencia, pieza, condición, ubicación y origen.
- Existe un mapa SVG 2D interactivo en la ficha del vehículo, con API y slots.
- La operación de línea 1995 crea inventario; la prueba de línea 232 verifica esa creación.
- No se encontraron dependencias ni activos propios de un visor 3D.

### Pendiente o no demostrable con el repositorio inspeccionado

- Un modelo tridimensional de sedán listo para producción.
- Un runtime 3D y controles de cámara.
- Mapping completo de cada repuesto a geometría 3D.
- Que los archivos visuales estáticos antiguos se carguen en alguna ruta no localizada dinámicamente; no hay referencias estáticas comprobadas.
- Cobertura visual real de los 106 ítems del sedán.
- Comportamiento 3D, porque hoy no existe implementación que pueda probarse.

## Archivos principales auditados

- `taller/desarme/catalogo_piezas.py`
- `taller/catalogos/catalogo_piezas_desarme_usa.py`
- `taller/desarme/catalogo_operativo.py`
- `taller/desarme/services.py`
- `taller/desarme/selectors/sesion_despiece.py`
- `taller/desarme/views.py`
- `taller/models/vehiculo_desarme.py`
- `taller/models/sugerencia_pieza_desarme.py`
- `taller/models/pieza_desarme.py`
- `taller/models/vehiculo_desarme_event.py`
- `templates/taller/desarme/ver_vehiculo.html`
- `templates/taller/desarme/partials/_vehiculo_mapa_visual.html`
- `templates/taller/desarme/partials/vehicles/*_wireframe.html`
- `static/js/desarme/vehicle-map.js`
- `static/js/desarme/piece-drawer.js`
- `static/taller/desarme/vehicle-map.css`
- `static/taller/desarme/svg/sedan_lateral.svg`
- `taller/tests/test_p3_sesion_visual.py`
- `taller/tests/test_desarme_mapa_visual_api.py`

