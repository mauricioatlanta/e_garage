# Desarme – Fase 2.5: Pulido operativo

Mejoras de usabilidad del módulo Desarme antes de dashboards y reportes avanzados.

---

## Archivos tocados

| Archivo | Cambio |
|---------|--------|
| `taller/desarme/views.py` | Búsqueda (q) y filtro estado en lista_vehiculos; annotate `piezas_count`; lista_vehiculos devuelve `q`, `estado_filtro`, `estados`. ver_vehiculo devuelve `piezas_activas_count`, `piezas_vendidas_count`. lista_piezas: búsqueda por código/nombre, filtros estado y vehiculo; devuelve `q`, `estado_filtro`, `vehiculo_filtro`, `vehiculos_choices`, `estado_pieza_choices`. |
| `taller/desarme/forms.py` | Reorden de campos; constantes `VEHICULO_DESARME_PRINCIPALES` / `OPCIONALES` y `PIEZA_DESARME_PRINCIPALES` / `OPCIONALES`; placeholders y `input-desarme` en widgets; campos opcionales con `required=False`. |
| `templates/taller/desarme/lista_vehiculos.html` | Barra de búsqueda (patente/VIN/marca/modelo) y filtro por estado; badge con cantidad de piezas por vehículo; botones “Inventario” y “Nueva pieza” en cada tarjeta; enlace “Limpiar” cuando hay filtros. |
| `templates/taller/desarme/lista_piezas.html` | Búsqueda por código/nombre; filtros estado y vehículo; badge de estado con estilos (DISPONIBLE, RESERVADA, VENDIDA, DANADA, SCRAP); bloque “Vehículo origen” con enlace al inventario. |
| `templates/taller/desarme/ver_vehiculo.html` | Resumen operativo: tarjetas con piezas activas, piezas vendidas (si hay), costo adquisición; botones de acción destacados (Editar vehículo, Ver inventario, Nueva pieza, Listado). |
| `templates/taller/desarme/vehiculo_form.html` | Secciones “Identificación y datos de desarme” y “Más opciones” (colapsable) con color, motor, caja, marca/modelo texto; estilos `.input-desarme` y `.form-desarme`. |
| `templates/taller/desarme/pieza_form.html` | Secciones “Vehículo e identificación”, “Precios y estado” y “Más opciones” (lado, zona, posición) colapsable; mismos estilos que vehiculo_form. |

---

## Mejoras aplicadas

### Listado de vehículos de desarme
- **Búsqueda**: parámetro `q` en patente, VIN, marca (FK y texto), modelo (FK y texto).
- **Filtro**: `estado` por `estado_desarme` (valores distintos existentes en BD).
- **Cantidad de piezas**: cada tarjeta muestra un badge “N piezas” (`annotate(piezas_count=Count('piezas_desarme'))`).
- **Accesos rápidos**: en cada tarjeta, botones “Inventario” y “Nueva pieza” además de Ver/Editar.
- **Limpiar**: enlace para quitar búsqueda y filtros.

### Listado de piezas
- **Búsqueda**: parámetro `q` en código y nombre.
- **Filtros**: `estado` (estado_pieza) y `vehiculo` (dropdown con vehículos de desarme).
- **Vehículo origen**: en cada tarjeta se muestra “Vehículo: [patente/vin]” con enlace al inventario de ese vehículo.
- **Badges por estado**: colores por estado (Disponible, Reservada, Vendida, Dañada, Scrap).

### Detalle de vehículo
- **Resumen operativo**: tarjetas con número de piezas activas, piezas vendidas (si > 0) y costo de adquisición (si existe).
- **Botones de acción**: más visibles (Editar vehículo, Ver inventario, Nueva pieza, Listado) con estilos diferenciados.

### Formularios
- **Orden y agrupación**: campos principales primero; opcionales en bloque “Más opciones” colapsable.
- **Vehículo**: identificación + datos de desarme (patente, VIN, marca, modelo, año, costo, fecha ingreso, estado, ubicación, observaciones); opcionales: marca_texto, modelo_texto, color, motor, caja.
- **Pieza**: vehículo + identificación (código, nombre, cantidad); precios y estado (costo, precio sugerido, estado, fecha extracción, ubicación, observaciones); opcionales: lado, zona, posición.
- **Claridad**: placeholders donde aplica; inputs con clase `input-desarme` y estilo coherente con el panel.

---

## Checklist manual de revisión visual/funcional

### Listado de vehículos
- [ ] La búsqueda por patente/VIN/marca/modelo filtra correctamente.
- [ ] El desplegable “Estado” muestra solo valores existentes y el filtro aplica.
- [ ] Cada tarjeta muestra la cantidad de piezas asociadas.
- [ ] Los botones “Inventario” y “Nueva pieza” llevan a la URL correcta (inventario del vehículo y alta de pieza con vehículo preseleccionado).
- [ ] “Limpiar” quita `q` y `estado` y muestra todos los vehículos.
- [ ] Sin resultados se muestra mensaje adecuado y enlace “Ver todos” o “Crear el primero”.

### Listado de piezas
- [ ] La búsqueda por código o nombre filtra correctamente.
- [ ] Los filtros por estado y por vehículo funcionan y se pueden combinar.
- [ ] Cada tarjeta muestra el vehículo origen con enlace al inventario.
- [ ] Los badges de estado se ven con el color correcto (Disponible, Reservada, Vendida, Dañada, Scrap).
- [ ] “Limpiar” restablece listado completo.

### Detalle de vehículo
- [ ] El resumen muestra piezas activas, piezas vendidas (si hay) y costo adquisición (si existe).
- [ ] Los botones “Editar vehículo”, “Ver inventario”, “Nueva pieza” y “Listado” son claros y funcionan.
- [ ] La tabla de piezas y el resto del contenido se ven correctos.

### Formularios
- [ ] Vehiculo: los campos principales están en el orden indicado; “Más opciones” se abre/cierra y contiene color, motor, caja, marca_texto, modelo_texto.
- [ ] Pieza: secciones “Vehículo e identificación”, “Precios y estado” y “Más opciones” (lado, zona, posición) correctas.
- [ ] Los inputs tienen estilo coherente (fondo oscuro, borde cyan).
- [ ] Guardar y Cancelar funcionan; al crear pieza con `?vehiculo=` el vehículo viene preseleccionado y bloqueado.

### General
- [ ] No se han introducido errores en listados sin filtros (vehículos/piezas vacíos o con datos).
- [ ] Coherencia visual con el resto de eGarage (colores, tipografía, espaciado).

---

## No incluido en esta fase

- Dashboards ni KPIs avanzados.
- Kanban.
- Reportes de rentabilidad complejos.
