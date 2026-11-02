# Páginas de entrada posibles para el suscriptor (post-login)

## Por qué llegas a centro-operaciones

Tras el login, el sistema te envía a **workspace** (`/us/en/workspace/`). La vista que atiende esa ruta es `ingreso_centro` (alias `centro_trabajo`), y **redirige siempre** a centro-operaciones cuando la URL contiene `"workspace"`. Por eso terminas en `/us/en/centro-operaciones/`.

- **Lugar de la redirección:** `taller/views_ingreso.py` → `ingreso_centro()` (líneas 9–16).

---

## Lista de templates posibles como página de entrada

Estas son las vistas que **sí renderizan una plantilla** y pueden usarse como página de entrada del suscriptor:

| # | Nombre lógico | URL (ej. USA) | URL (ej. Chile) | Vista | Template(s) |
|---|----------------|---------------|------------------|--------|-------------|
| 1 | **Centro de operaciones** (actual) | `/us/en/centro-operaciones/` | `/cl/es/centro-operaciones/` | `dashboard_centro_operaciones` | `dashboard/centro_operaciones.html` (resolución por país/idioma vía `select_country_lang_template`). Ej: `taller/cl/es/dashboard/centro_operaciones.html`, `taller/common/dashboard/centro_operaciones.html`. |
| 2 | **Centro de operaciones espacial** | `/us/en/centro-operaciones-espacial/` | `/cl/es/centro-operaciones-espacial/` | `dashboard_centro_operaciones_espacial` | USA: `taller/us/en/dashboard/centro_operaciones_espacial.html`. Otros: `dashboard/centro_operaciones_espacial.html` (resolución por país/idioma). |
| 3 | **Dashboard genérico** | `/us/en/dashboard/` | `/cl/es/dashboard/` | `dashboard` | No usa template propio: **redirige** a centro_operaciones (CL) o centro_operaciones_espacial (USA). No sirve como entrada final sin tocar esa redirección. |
| 4 | **Dashboard Chile** | — | `/cl/es/dashboard/` (si se usara) | — | `cl/es/dashboard/dashboard_chile.html` (referido en rutas/otros proyectos). |
| 5 | **Workspace / Centro de trabajo** | `/us/en/workspace/` | `/cl/es/workspace/` | `ingreso_centro` (alias `centro_trabajo`) | **Hoy no renderiza:** solo redirige a centro-operaciones. Para usarlo como entrada habría que quitar esa redirección y asignar una plantilla a esta vista. |

---

## Templates de dashboard/entrada en el proyecto

Rutas de archivo en `templates/` (o equivalentes):

- `taller/dashboard/centro_operaciones.html` (global)
- `taller/common/dashboard/centro_operaciones.html`
- `taller/common/dashboard/centro_operaciones_espacial.html`
- `cl/es/dashboard/centro_operaciones.html`
- `cl/es/dashboard/centro_operaciones_espacial.html`
- `cl/es/dashboard/dashboard_chile.html`
- `us/en/dashboard/centro_operaciones_espacial.html`
- `us/en/dashboard/centro_operaciones_espacial_alt.html`
- `taller/us/es/dashboard/centro_operaciones_espacial.html`
- `taller/dashboard/dashboard.html`
- `taller/dashboard/home.html`
- `ar/es/dashboard/dashboard_chile.html`
- `uy/es/dashboard/centro_operaciones.html`
- `uy/es/dashboard/centro_operaciones_espacial.html`

---

## Dónde se define la entrada post-login

- **Adaptador de login (destino después de iniciar sesión):**  
  `taller/views_extra/account_adapter.py`  
  - Método: `get_login_redirect_url()`.  
  - Para USA usa `reverse("us_en:centro_trabajo")` → `/us/en/workspace/`.  
  - Para Chile usa `_reverse_by_country("CL", "centro_trabajo")` → `/cl/es/workspace/` (según rutas de Chile).  
  - Como **workspace** redirige a centro-operaciones, el usuario termina en **centro-operaciones**.

- **Redirección workspace → centro-operaciones:**  
  `taller/views_ingreso.py` → `ingreso_centro()`.

---

## Cómo elegir la página de entrada correcta

1. **Mantener centro-operaciones como entrada**  
   No hace falta cambiar nada: ya es a donde se llega por la redirección desde workspace.

2. **Usar centro-operaciones espacial como entrada (solo USA)**  
   En `account_adapter.py`, para USA devolver la URL de `centro_operaciones_espacial` en lugar de `centro_trabajo` (por ejemplo `us_en:centro_operaciones_espacial` si existe en tus URLs).

3. **Usar workspace como entrada (sin redirigir a centro-operaciones)**  
   - En `account_adapter.py` ya se envía a `centro_trabajo` (workspace).  
   - En `taller/views_ingreso.py`, quitar o condicionar la redirección de `ingreso_centro` a centro-operaciones y hacer que esa vista renderice la plantilla que quieras (p. ej. una home o un dashboard propio de “centro de trabajo”).

4. **Otra plantilla como entrada**  
   Asignar una vista que renderice el template elegido y, en `get_login_redirect_url()`, hacer que devuelva la URL de esa vista (por nombre de ruta o `reverse()`).

---

## Resumen

- La “entrada” que ves ahora es **centro de operaciones** porque **workspace** redirige ahí.
- Las opciones que tienen template propio y pueden ser entrada son sobre todo: **centro_operaciones** (1) y **centro_operaciones_espacial** (2). **Workspace** (5) puede serlo si dejas de redirigir y le asignas un template.
- Para cambiar la página de entrada del suscriptor se modifican:  
  - `taller/views_extra/account_adapter.py` (destino post-login) y, si quieres que workspace sea la entrada,  
  - `taller/views_ingreso.py` (comportamiento de `ingreso_centro`).
