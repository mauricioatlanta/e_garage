# Componentes e identificadores — sedan_v01

Convención: unidades métricas; X hacia el frente, Y hacia la izquierda del conductor, Z hacia arriba. `left` y `right` siempre se interpretan desde la perspectiva del conductor.

## Identificadores principales conservados en GLB

### Carrocería

- `body.shell`
- `body.roof_panel`
- `body.door.front.left`
- `body.door.front.right`
- `body.door.rear.left`
- `body.door.rear.right`
- `body.hood`
- `body.trunk_lid`
- `body.bumper.front`
- `body.bumper.rear`
- `body.mirror.left`
- `body.mirror.right`

Los pivotes de las puertas están colocados en el borde delantero correspondiente. El pivote del capó está en su borde posterior y el de la tapa de maletero en su borde delantero. Esto prepara aperturas futuras, pero no incluye animaciones.

### Cristales

- `glass.windshield.front`
- `glass.windshield.rear`
- `glass.door.front.left`
- `glass.door.front.right`
- `glass.door.rear.left`
- `glass.door.rear.right`

### Iluminación

- `light.headlamp.left`
- `light.headlamp.right`
- `light.tail.left`
- `light.tail.right`

### Ruedas

- `wheel.front.left`
- `wheel.front.right`
- `wheel.rear.left`
- `wheel.rear.right`

Cada rueda tiene objetos auxiliares `.rim`, `.hub` y `.spoke.NN`.

### Interior

- `interior.seat.front.left`
- `interior.seat.front.right`
- `interior.seat.rear`
- `interior.dashboard`
- `interior.steering_wheel`

### Mecánica simplificada

- `engine.assembly`
- `cooling.radiator`
- `cooling.fan`
- `cooling.water_pump`

## Alcance del mapeo

Estos identificadores son una propuesta artística y técnica para el modelo. No sustituyen ni migran los `visual_slot` existentes y no pretenden cubrir los 106 repuestos sugeridos para sedán. Los detalles sin `component_id` son geometría auxiliar del modelo, no slots de inventario.

