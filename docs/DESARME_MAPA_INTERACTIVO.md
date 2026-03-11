# Mapa Interactivo de Vehículo para Desarme

## Archivos creados / modificados

### Backend
| Archivo | Descripción |
|---------|-------------|
| `taller/views_desarme/__init__.py` | Módulo desarme, exporta vistas |
| `taller/views_desarme/mapa.py` | Vista principal y endpoints AJAX |
| `taller/views_desarme.py` | **Eliminado** – reemplazado por package |
| `taller/urls.py` | Rutas desarme actualizadas |

### Templates
| Archivo | Descripción |
|---------|-------------|
| `templates/taller/desarme/mapa_piezas.html` | Template principal |
| `templates/taller/desarme/partials/_header_desarme.html` | Header con KPIs |
| `templates/taller/desarme/partials/_piece_drawer_desarme.html` | Panel lateral de pieza |
| `templates/taller/desarme/partials/_footer_desarme.html` | Resumen inferior |
| `templates/taller/desarme/svg/_vehicle_front.html` | SVG vista frontal |
| `templates/taller/desarme/svg/_vehicle_left.html` | SVG vista lateral izq |

### Estáticos
| Archivo | Descripción |
|---------|-------------|
| `static/taller/desarme/vehicle-map.css` | Estilos del mapa |
| `static/js/desarme/vehicle-map.js` | Lógica del mapa |
| `static/js/desarme/piece-drawer.js` | Panel lateral y guardado |
| `static/js/desarme/desarme-summary.js` | Resumen y progreso |

## URLs

- `GET /desarme/vehiculos/<pk>/mapa/` – Vista principal
- `GET|POST /desarme/vehiculos/<pk>/pieza-por-zona/` – Obtener/crear/actualizar pieza
- `GET /desarme/vehiculos/<pk>/resumen-json/` – KPIs y resumen actualizado

## API pieza-por-zona

**GET** `?zone=left_front_door&view=left`  
Respuesta: pieza si existe, o `{exists: false}`

**POST** JSON:
```json
{
  "zone": "left_front_door",
  "view": "lateral_izq",
  "piece_name": "Puerta delantera izquierda",
  "estado_pieza": "disponible",
  "precio_venta": "120000",
  "stock": 1,
  "observacion_estado": "abolladura menor"
}
```
Acepta también: `zona`, `vista`, `nombre`, `observaciones` (compatibilidad).

## Cómo probar

1. Tener un vehículo con `tipo_uso="desarme"`.
2. Ir a `/desarme/vehiculos/<id>/mapa/` (o la ruta con prefijo país si aplica).
3. Clic en una zona del SVG → se abre el panel lateral.
4. Rellenar estado, precio, observación y Guardar.
5. La zona se colorea según estado; el resumen se actualiza.

## Nota sobre modelo Repuesto

El modelo usa el campo `observaciones` (no `observacion_estado`). La API acepta ambos nombres y persiste en `observaciones`.
