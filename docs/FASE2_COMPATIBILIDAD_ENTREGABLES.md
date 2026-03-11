# Ajustes de compatibilidad Fase 2 – Desarmaduría

Correcciones puntuales para namespaces dinámicos, empresa activa y render de datos, **sin rehacer** la Fase 2.

---

## A. Resumen de los ajustes

1. **Namespaces dinámicos (vistas)**  
   Se añadió `get_country_ns_from_path(path)` en `taller/utils/url_helpers.py`, alineado con `_country_ns_from_path` del tag `country_url`, y se actualizó `reverse_country(request, view_path, ...)` para usarlo. Las vistas de desarme que hacían `reverse("taller:desarme:...")` o `redirect("taller:desarme:...")` pasan a usar `reverse_country(request, "desarme:...", kwargs={...})`, de modo que la URL se resuelve con el namespace del país/idioma actual (chile, us_en, us_es, usa).

2. **Namespaces en templates**  
   Todas las referencias `{% url 'taller:desarme:...' %}`, `{% url 'taller:repuestos:...' %}` y `{% url 'taller:vehiculos:...' %}` en templates del módulo desarme se sustituyeron por `{% country_url 'desarme:...' %}`, `{% country_url 'repuestos:...' %}` y `{% country_url 'vehiculos:...' %}` (con `{% load country_url %}` donde faltaba).

3. **Empresa activa**  
   En las vistas de desarme que ya existían (`plantillas`, `cierre`) se seguía usando `get_or_create_empresa(request)`; no se usaba `request.user.empresa` solo. No se cambió lógica de empresa en este paso. **Si añades vistas Fase 2** (home, lista vehículos desarme, crear vehículo desarme), hay que usar siempre `get_or_create_empresa(request)` para obtener la empresa activa y no depender solo de `request.user.empresa`.

4. **Marca / modelo en listados**  
   El modelo `Vehiculo` ya define `get_marca_display()` y `get_modelo_display()` (prioridad `marca_texto`/`modelo_texto`, luego FK `marca`/`modelo`, luego "Sin marca"/"Sin modelo"). Los templates que usan `{{ vehiculo.get_marca_display }}` y `{{ vehiculo.get_modelo_display }}` son correctos. **Si añades** `vehiculos_list.html` (listado de vehículos de desarme), usa esos mismos métodos para cada vehículo.

---

## B. Archivos modificados

| Archivo |
|--------|
| `taller/utils/url_helpers.py` |
| `taller/views_desarme/plantillas.py` |
| `taller/views_desarme/cierre.py` |
| `templates/taller/desarme/partials/_header_desarme.html` |
| `templates/taller/desarme/partials/_header_kpis.html` |
| `templates/taller/desarme/dashboard_financiero.html` |
| `templates/taller/desarme/cierre_vehiculo_form.html` |
| `templates/taller/desarme/plantillas/plantilla_aplicar.html` |
| `templates/taller/desarme/plantillas/plantilla_detail.html` |
| `templates/taller/desarme/plantillas/plantilla_list.html` |
| `templates/taller/desarme/plantillas/plantilla_form.html` |

---

## C. Código de los archivos modificados

### 1. `taller/utils/url_helpers.py`

- **Nuevo:** `get_country_ns_from_path(path)`  
  Devuelve el namespace de país según el path (`/us/en/` → `us_en`, `/us/es/` → `us_es`, `/us/` → `usa`, `/cl/` → `chile`), coherente con `country_url`.

- **Cambio en:** `reverse_country(request, view_path, app_namespace="taller", *args, **kwargs)`  
  Usa `country_ns = get_country_ns_from_path(getattr(request, "path", None) or "/")` y construye `full_name = f"{country_ns}:{app_namespace}:{view_path}"` antes de `reverse(full_name, args=args, kwargs=kwargs)`.

### 2. `taller/views_desarme/plantillas.py`

- Import: `from taller.utils.url_helpers import reverse_country` (se quitó `from django.urls import reverse`).
- Redirect cuando vehículo cerrado: `return redirect(reverse_country(request, "vehiculos:ver_vehiculo", kwargs={"vehiculo_id": vehiculo.pk}))`.
- Tras aplicar plantilla: `mapa_url = reverse_country(request, "desarme:mapa_piezas", kwargs={"pk": vehiculo.pk})`, `repuestos_url = reverse_country(request, "repuestos:lista_repuestos")`, `vehiculo_url = reverse_country(request, "vehiculos:ver_vehiculo", kwargs={"vehiculo_id": vehiculo.pk})`, y `return redirect(mapa_url)`.

### 3. `taller/views_desarme/cierre.py`

- Import: `from taller.utils.url_helpers import reverse_country`.
- Ambos redirects a dashboard: `return redirect(reverse_country(request, "desarme:dashboard_financiero", kwargs={"pk": vehiculo.pk}))`.

### 4. Templates

En todos los que se tocan:

- Se añade `country_url` al `{% load ... %}` donde faltaba.
- Sustituciones:
  - `{% url 'taller:desarme:mapa_piezas' pk=vehiculo.pk %}` → `{% country_url 'desarme:mapa_piezas' pk=vehiculo.pk %}`
  - `{% url 'taller:desarme:dashboard_financiero' pk=vehiculo.pk %}` → `{% country_url 'desarme:dashboard_financiero' pk=vehiculo.pk %}`
  - `{% url 'taller:desarme:cerrar_vehiculo' pk=vehiculo.pk %}` → `{% country_url 'desarme:cerrar_vehiculo' pk=vehiculo.pk %}`
  - `{% url 'taller:desarme:aplicar_plantilla' pk=vehiculo.pk %}` → `{% country_url 'desarme:aplicar_plantilla' pk=vehiculo.pk %}`
  - `{% url 'taller:desarme:plantilla_list' %}` → `{% country_url 'desarme:plantilla_list' %}`
  - `{% url 'taller:desarme:plantilla_create' %}` → `{% country_url 'desarme:plantilla_create' %}`
  - `{% url 'taller:desarme:plantilla_detail' pk=p.pk %}` → `{% country_url 'desarme:plantilla_detail' pk=p.pk %}`
  - `{% url 'taller:desarme:plantilla_edit' pk=... %}` → `{% country_url 'desarme:plantilla_edit' pk=... %}`
  - `{% url 'taller:repuestos:lista_repuestos' %}?vehiculo_origen=...` → `{% country_url 'repuestos:lista_repuestos' %}?vehiculo_origen=...`
  - `{% url 'taller:vehiculos:ver_vehiculo' vehiculo.pk %}` → `{% country_url 'vehiculos:ver_vehiculo' vehiculo.pk %}` (y equivalente con `vehiculo_id=vehiculo.pk` donde aplicara, unificado a un solo arg posicional).

---

## D. Por qué mejoran la compatibilidad

- **Multi-country / multi-idioma:** Las URLs de desarme, repuestos y vehículos dejan de depender del namespace fijo `taller:`. Se resuelven con el mismo criterio que el resto del proyecto (chile, us_en, us_es, usa), de modo que /cl/es/... y /us/en/... generan enlaces correctos sin hardcodear `taller:`.
- **Una sola fuente de verdad para el namespace:** `get_country_ns_from_path` replica la lógica de `_country_ns_from_path` del tag `country_url`, de forma que vistas y templates generan las mismas URLs para la misma ruta.
- **Empresa:** Las vistas que ya usaban `get_or_create_empresa(request)` se mantienen; si en el futuro se añaden home/lista/crear vehículo desarme, deben usar la misma función para alinear con middleware/sesión y no depender solo de `request.user.empresa`.
- **Marca/modelo:** Usar `get_marca_display`/`get_modelo_display` es correcto con FK y con `marca_texto`/`modelo_texto`; no hace falta cambiar los templates existentes ni el futuro `vehiculos_list.html` si usa esos métodos.

---

## E. Riesgos y notas menores

- **Fase 2 (home, lista vehículos, crear vehículo):** En este repositorio no existen aún `views_desarme/home.py`, `views_desarme/vehiculos.py` ni los templates `home.html` y `vehiculos_list.html`. Si los añades, aplica en vistas `reverse_country(request, "desarme:...", kwargs={...})` y `get_or_create_empresa(request)`, y en templates `{% country_url 'desarme:...' %}` y `{{ v.get_marca_display }} {{ v.get_modelo_display }}` para cada vehículo.
- **`vehiculos:ver_vehiculo`:** La ruta usa `<int:vehiculo_id>/`. Con `country_url` se llama como `{% country_url 'vehiculos:ver_vehiculo' vehiculo.pk %}` (un argumento posicional); `reverse_country` con `kwargs={"vehiculo_id": vehiculo.pk}` es equivalente.
- **Lista general de vehículos:** Sigue usando `desarme_map_url_name` calculado desde `request.resolver_match.namespace` en `vehiculos/views_fbv.py`; no se modificó en esta tanda.

Con estos cambios, el flujo (home desarme → listado vehículos desarme → crear → mapa → dashboard → repuestos filtrados → cerrar) queda alineado con la arquitectura multi-país/idioma del proyecto.
