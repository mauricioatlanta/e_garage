# Mapa Interactivo de Desarme - Capa Visual Frontend

## Archivos creados/modificados

### Template
| Ruta | Descripción |
|------|-------------|
| `templates/taller/desarme/demo_mapa.html` | Página demo con layout completo y datos mock |

### SVGs
| Ruta | Descripción |
|------|-------------|
| `templates/taller/desarme/svg/_vehicle_front.html` | Vista frontal: capot, parrilla, focos, neblineros, parachoques |
| `templates/taller/desarme/svg/_vehicle_left.html` | Vista lateral: espejo, puertas, tapabarros, vidrios, llantas |

### JS
| Ruta | Descripción |
|------|-------------|
| `static/js/desarme/vehicle-map.js` | Hover, tooltip, selección, tabs, pintado de estados |
| `static/js/desarme/piece-drawer.js` | Panel lateral, guardar en memoria, refrescar zona |

### CSS
| Ruta | Descripción |
|------|-------------|
| `static/taller/desarme/vehicle-map.css` | Estilos premium: KPI cards, tabs, drawer, tooltip, pills |

### Backend (mínimo)
| Ruta | Descripción |
|------|-------------|
| `taller/views_desarme/mapa.py` | Vista `demo_mapa_desarme` |
| `taller/urls.py` | Ruta `/desarme/demo/` |

---

## Cómo probar

1. Iniciar servidor: `python manage.py runserver`
2. Iniciar sesión
3. Ir a `/desarme/demo/` (o `/<country>/<lang>/desarme/demo/` según tu routing)

---

## Interacción

1. **Tabs**: Clic en "Frontal" o "Lateral izquierda" cambia el SVG visible.
2. **Hover**: Al pasar el mouse sobre una zona aparece un tooltip con nombre y estado.
3. **Click**: Selecciona la zona, la resalta con borde cyan y abre el panel lateral.
4. **Panel**: Muestra nombre, zona, vista; selector de estado; precio, stock, observación.
5. **Guardar**: Persiste en memoria (`piecesByZone`), repinta la zona y actualiza el footer.
6. **Guardar y siguiente**: Guarda y abre la siguiente zona de la vista actual.
7. **Marcar scrap**: Pone estado "Scrap" con un clic.
8. **Cerrar**: Botón × cierra el panel y muestra el estado vacío.

---

## Conexión con backend real

1. **Datos iniciales**: Reemplazar `DESARME_CONFIG.piecesByZone` por datos del servidor (ej. `repuestos` con `zona_mapa`, `vista_mapa`, `estado_pieza`, etc.).
2. **Guardar**: En el handler de "Guardar", añadir `fetch(POST api_pieza_url, body)` en lugar de solo `setPiece()`.
3. **Resumen**: Tras guardar, llamar a `GET resumen-json` y actualizar KPIs del header y footer.
4. **CSRF**: Usar `DESARME_CONFIG.csrf` en las peticiones POST.
5. **canEdit**: Si `canEdit: false`, deshabilitar inputs y botones del drawer.
