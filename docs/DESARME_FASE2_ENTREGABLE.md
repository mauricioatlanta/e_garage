# Desarme – Fase 2: Entregable

## Plan de archivos tocados

| Archivo | Cambio |
|---------|--------|
| `taller/urls_desarme.py` | Rutas reales: index, vehiculos (listar/crear/ver/editar/inventario), piezas (listar/crear/editar). |
| `taller/desarme/__init__.py` | Nuevo paquete desarme. |
| `taller/desarme/views.py` | Vistas FBV: index, lista_vehiculos, crear_vehiculo, ver_vehiculo, editar_vehiculo, lista_piezas, crear_pieza, editar_pieza, inventario_vehiculo. |
| `taller/desarme/forms.py` | VehiculoDesarmeForm (tipo_uso=DESARME, sin cliente), PiezaDesarmeForm. |
| `templates/taller/desarme/lista_vehiculos.html` | Listado de vehículos de desarme. |
| `templates/taller/desarme/ver_vehiculo.html` | Detalle vehículo + tabla de piezas. |
| `templates/taller/desarme/vehiculo_form.html` | Alta/edición vehículo desarme. |
| `templates/taller/desarme/lista_piezas.html` | Listado de piezas (opcional filtro ?vehiculo=). |
| `templates/taller/desarme/pieza_form.html` | Alta/edición pieza (opcional ?vehiculo= para preselección). |
| `templates/taller/desarme/inventario_vehiculo.html` | Inventario por vehículo. |
| `templates/taller/layout/sidebar.html` | Enlace “Desarme” al listado de vehículos. |

---

## Rutas del módulo Desarme

- `GET /desarme/` → redirige a lista de vehículos.
- `GET /desarme/vehiculos/` → listado vehículos de desarme.
- `GET|POST /desarme/vehiculos/crear/` → alta vehículo desarme.
- `GET /desarme/vehiculos/<pk>/` → detalle vehículo.
- `GET|POST /desarme/vehiculos/<pk>/editar/` → editar vehículo.
- `GET /desarme/vehiculos/<pk>/inventario/` → inventario de piezas del vehículo.
- `GET /desarme/piezas/` → listado piezas (opcional `?vehiculo=<id>`).
- `GET|POST /desarme/piezas/crear/` → alta pieza (opcional `?vehiculo=<id>`).
- `GET|POST /desarme/piezas/<pk>/editar/` → editar pieza.

Con prefijo de país/idioma: p. ej. `/cl/es/desarme/...` o `/us/en/desarme/...` según configuración.

---

## Vistas implementadas

- **index**: redirección a `desarme:lista_vehiculos`.
- **lista_vehiculos**: `Vehiculo` con `empresa` del usuario y `tipo_uso=DESARME`.
- **crear_vehiculo / editar_vehiculo**: `VehiculoDesarmeForm`; en guardar se fuerza `tipo_uso=DESARME` y `cliente=None`.
- **ver_vehiculo**: detalle del vehículo y listado de `piezas_desarme` activas.
- **lista_piezas**: `PiezaDesarme` de la empresa; filtro opcional por `vehiculo_id` (GET `vehiculo`).
- **crear_pieza / editar_pieza**: `PiezaDesarmeForm`; si viene `?vehiculo=<id>` se preselecciona y bloquea el vehículo.
- **inventario_vehiculo**: piezas del vehículo con enlaces a editar pieza y a “Nueva pieza” para ese vehículo.

Todas las vistas requieren login y filtran por `request.user.empresa`.

---

## Templates implementados

- **lista_vehiculos.html**: grid de tarjetas (patente/vin, marca/modelo, año, estado, ubicación), botones Ver / Editar / Inventario y acciones “Nuevo vehículo desarme” y “Piezas”.
- **ver_vehiculo.html**: datos del vehículo (patente, VIN, año, estado, ubicación, ingreso, costo, observaciones) y tabla de piezas con enlace a editar y a “Nueva pieza”.
- **vehiculo_form.html**: formulario genérico para campos del vehículo desarme (patente, vin, marca, modelo, año, color, motor, caja, costo, fecha ingreso, estado, ubicación, observaciones).
- **lista_piezas.html**: grid de piezas (código, nombre, estado, vehículo) con Editar e Inventario.
- **pieza_form.html**: formulario pieza (vehiculo, codigo, nombre, cantidad, costos, precio sugerido, estado, ubicación, observaciones, lado/zona/posicion).
- **inventario_vehiculo.html**: resumen del vehículo y tabla de piezas con cantidades, costos y enlace a editar.

Diseño: mismo layout que el resto del panel (`base_egarage_panel`), estilos compactos y coherentes (cyan/púrpura, tarjetas, botones).

---

## Navegación

- En **sidebar** (`templates/taller/layout/sidebar.html`) se añadió un enlace con icono “Desarme” que apunta a `desarme:lista_vehiculos` (vía `country_url`).
- Desde listados y detalle hay enlaces cruzados: Vehículos ↔ Piezas, Ver ↔ Editar ↔ Inventario, “Nueva pieza” con vehículo preseleccionado cuando aplica.

---

## Checklist de pruebas manuales

1. **Acceso al módulo**
   - [ ] Entrar con usuario con empresa. Desde sidebar, clic en Desarme y comprobar que se abre el listado de vehículos de desarme (o vacío).
   - [ ] Comprobar que la URL es la esperada (p. ej. `/cl/es/desarme/vehiculos/` o equivalente según país).

2. **Vehículos de desarme**
   - [ ] Crear vehículo de desarme: patente (o VIN), marca/modelo, año, opcionalmente costo, fecha ingreso, estado, ubicación. Guardar y comprobar que aparece en el listado y que es tipo DESARME (sin cliente).
   - [ ] Ver detalle: comprobar datos y que la sección de piezas está vacía o muestra las ya creadas.
   - [ ] Editar vehículo: cambiar algún campo y guardar; comprobar que se actualiza.

3. **Piezas de desarme**
   - [ ] Desde detalle de vehículo, “Nueva pieza”: comprobar que el vehículo viene preseleccionado y bloqueado. Guardar código, nombre, cantidad, etc. Comprobar que la pieza aparece en el detalle del vehículo y en “Inventario”.
   - [ ] Desde “Piezas” en el menú, “Nueva pieza” sin `?vehiculo=`: elegir vehículo de desarme y guardar.
   - [ ] Editar una pieza y comprobar que los cambios se guardan y se ven en inventario y listado de piezas.

4. **Inventario por vehículo**
   - [ ] En listado de vehículos, clic en “Inventario” de un vehículo. Comprobar que se listan solo las piezas de ese vehículo y que “Nueva pieza” abre el formulario con ese vehículo preseleccionado.

5. **Seguridad y filtros**
   - [ ] Comprobar que solo se ven vehículos/piezas de la empresa del usuario.
   - [ ] Comprobar que en este módulo solo aparecen vehículos con `tipo_uso=DESARME` (los de cliente no deben listarse aquí).

6. **Navegación y diseño**
   - [ ] Verificar que todos los enlaces (Listado, Ver, Editar, Inventario, Piezas, Vehículos) llevan a la pantalla correcta.
   - [ ] Verificar que la interfaz se ve coherente con el resto de eGarage (colores, tipografía, espaciado).

---

## No incluido en esta fase (según alcance)

- Dashboards, KPIs, Kanban.
- Reportes avanzados.
- Centro de operaciones específico de desarme.
- Autocompletado avanzado para marca/modelo en el formulario de vehículo (se usa el formulario estándar del modelo).
