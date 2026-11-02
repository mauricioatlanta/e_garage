# Despliegue: Nombres traducibles y por empresa (Pieza Desarme i18n)

## Resumen de arquitectura

- **PiezaDesarmeName** (existente): nombre canónico global por idioma (es/en/pt) y aliases para búsqueda. No se elimina; se reutiliza.
- **PiezaDesarmeCompanyLabel** (nuevo): nombre visible preferido por empresa e idioma. Una fila por (empresa, pieza_desarme, language). Unique constraint en esos tres campos.
- **PiezaDesarme**:
  - `get_catalog_label(language)`: nombre desde PiezaDesarmeName (fallback es → en → español → self.nombre).
  - `get_company_label(empresa, language)`: nombre desde PiezaDesarmeCompanyLabel; si no hay, None.
  - `get_display_label(empresa, language)`: prioridad company → catalog → self.nombre (método único para mostrar en UI).
  - `get_search_terms(empresa, language)`: lista deduplicada para búsqueda (display, aliases, código, nombre).
- **API**: `POST api/piezas/<pk>/label-empresa/` con JSON `{ language, label, aliases }` para crear/actualizar el nombre visible por empresa.
- **UI**: En inventario vehículo, botón "Editar nombre" por tarjeta que abre modal y guarda vía fetch; búsqueda usa nombre visible y search_terms (aliases, sku, categoría).

No se elimina `p.nombre`; no se cambia lógica financiera ni documentos históricos.

---

## Archivos modificados / creados

| Archivo | Cambio |
|---------|--------|
| `taller/models/pieza_desarme.py` | Añadidos PiezaDesarmeCompanyLabel, get_catalog_label, get_company_label, get_display_label, get_search_terms; get_label delega a get_catalog_label. |
| `taller/models/__init__.py` | Export PiezaDesarmeCompanyLabel. |
| `taller/migrations/0090_pieza_desarme_company_label.py` | Nueva migración (solo PiezaDesarmeCompanyLabel). |
| `taller/desarme/views.py` | inventario_vehiculo: prefetch names+company_labels, piezas_json con get_display_label y search_terms; iniciar_venta: get_display_label en prefill; scanner: prefetch y display_nombre; ver_vehiculo: prefetch y display_nombre; api_pieza_label_empresa_guardar. |
| `taller/desarme/views_inventario.py` | inventario_inteligente: get_display_label y search_terms; _get_venta_session_data: display_nombre en resumen; mensajes con display_nombre. |
| `taller/urls_desarme.py` | Ruta `api/piezas/<int:pk>/label-empresa/`. |
| `templates/taller/desarme/inventario_vehiculo.html` | Modal "Editar nombre", botón por tarjeta, labelApiUrlPattern, currentLang, búsqueda con search_terms, saveLabel/openEditLabel/closeEditLabel. |
| `templates/taller/desarme/scanner_vehiculo.html` | data-nombre y título con display_nombre\|default:p.nombre. |
| `templates/taller/desarme/ver_vehiculo.html` | Columna nombre con display_nombre\|default:p.nombre. |
| `templates/taller/desarme/confirmar_venta_desde_inventario.html` | item.display_nombre\|default:item.repuesto.nombre. |
| `taller/admin.py` | PiezaDesarmeCompanyLabelAdmin (list_display, search, filters). |
| `taller/management/commands/backfill_pieza_desarme_i18n_labels.py` | Comando --dry-run y backfill es/en desde catálogo USA. |
| `taller/tests/test_pieza_desarme_i18n_labels.py` | Tests get_display_label, inventario, API guardar label. |

---

## Instrucciones de despliegue en servidor

1. **Migraciones**
   ```bash
   cd /ruta/al/proyecto
   source .venv/bin/activate   # o el entorno que uses
   python manage.py makemigrations taller --name pieza_desarme_company_label
   # Solo si no está ya generada la 0090
   python manage.py migrate taller
   ```

2. **Estáticos** (si aplica)
   ```bash
   python manage.py collectstatic --noinput
   ```

3. **Backfill (recomendado: primero en dry-run)**
   ```bash
   python manage.py backfill_pieza_desarme_i18n_labels --dry-run
   python manage.py backfill_pieza_desarme_i18n_labels
   ```

4. **Reinicio de servicios**
   ```bash
   sudo systemctl restart gunicorn    # o el proceso WSGI que uses
   sudo systemctl reload nginx       # si usas nginx delante
   ```

5. **Comprobaciones**
   - Entrar a inventario de un vehículo de desarme y comprobar que los nombres se ven según idioma.
   - En una tarjeta, "Editar nombre", cambiar texto y guardar; ver que se actualiza sin recargar.
   - Búsqueda por nombre/alias/sku/categoría en el mismo inventario.

---

## Notas

- La migración 0090 no toca otras tablas (se eliminaron operaciones sobre CorrelativoDocumento que venían en el makemigrations inicial).
- Si en local falla `migrate` por migraciones previas (p. ej. 0075), en servidor con BD al día la 0090 debería aplicarse bien.
- El comando de backfill no sobrescribe PiezaDesarmeName existentes; solo crea es con `p.nombre` y en cuando hay match por código en catálogo USA.
