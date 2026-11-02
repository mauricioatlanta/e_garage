# Reglas de stubs en eGarage

Documentación de las prácticas ya aplicadas implícitamente para vistas stub: cuándo usarlas, cómo implementarlas y qué evitar.

---

## 1. Qué es un stub y cuándo usarlo

- **Stub**: vista o API que responde con una respuesta mínima válida (HTTP 200 o similar) sin implementar la lógica real, para que las URLs sigan resolviendo y no se produzcan 500.
- **Cuándo**:
  - La ruta está en `urls.py` pero la vista real falla en el servidor (módulo dañado, dependencia faltante, `ImportError`, etc.).
  - La funcionalidad real no está desplegada aún pero se quiere mantener la estructura de URLs.
  - Hotfix urgente en producción: se reemplaza la vista problemática por un stub en lugar de tocar `urls.py`.

---

## 2. Reglas que aplicamos

### 2.1 No tocar `urls.py` para “ocultar” la ruta

- Las rutas en `urls.py` siguen apuntando a la misma vista; lo que se cambia es **la implementación de la vista** (por un stub), no la definición de la URL.
- Evita tener que modificar varios `include()` o `path()` y reduces riesgo de regresiones.

### 2.2 La vista debe existir y ser invocable

- El nombre de la vista y la firma deben coincidir con lo que espera `urls.py` (ej. `request`, o `request, *args, **kwargs` para mayor compatibilidad).
- Si la URL recibe argumentos o `kwargs`, el stub debe aceptarlos aunque no los use:  
  `def mi_vista(request, *args, **kwargs):`

### 2.3 Respuesta HTTP segura: 200 y cuerpo controlado

- **APIs (JSON)**:  
  `return JsonResponse({"ok": True, "detail": "nombre_stub"}, status=200)`  
  o, si se quiere marcar explícitamente que es temporal:  
  `{"ok": False, "stub": "nombre_stub"}` con `status=200` (evitar 4xx/5xx para no romper clientes que solo comprueban “respuesta OK”).
- **HTML/página**:  
  `return HttpResponse("Título (stub).", status=200)`
- No devolver 500, 404 ni 403 en stubs salvo que sea un requisito explícito del contrato de la API.

### 2.4 Decoradores y método HTTP

- Si la ruta está bajo `@require_GET` o `path(..., name='...')` que en la vista real usa `require_GET`, el stub también debe respetarlo para no provocar `405 Method Not Allowed`.
- Para clases basadas en vista (`View`), el stub debe implementar el método que usa la URL (p. ej. `get` o `post`):  
  `def get(self, request, *args, **kwargs): return JsonResponse({"ok": False, "stub": "AIInsightView"}, status=200)`

### 2.5 Comentario identificador en código

- Marcar el bloque con un comentario para facilitar búsqueda y futura sustitución por la vista real, por ejemplo:  
  `# --- HOTFIX: stubs para compatibilidad con urls.py ---`  
  o  
  `# Stub seguro para producción: evita 500 por rutas registradas`

---

## 3. Dónde se usan stubs hoy

### 3.1 Analytics (`taller.analytics`)

`analytics/urls.py` enlaza vistas que, en algunos entornos, se sustituyen por stubs:

| Vista / Clase       | Uso en `urls.py`                          | Comportamiento del stub                        |
|---------------------|--------------------------------------------|-----------------------------------------------|
| `dashboard_ai_view` | `""`, `"dashboard/"`                       | `HttpResponse("Dashboard AI (stub).", 200)`   |
| `revenue_analytics_api` | `"revenue-api/"`                      | `JsonResponse({"ok": True, "detail": "revenue_analytics_api stub"}, 200)` |
| `vehicle_analytics_api`  | `"vehicle-api/"`                      | `JsonResponse({"ok": False, "stub": "vehicle_analytics_api"}, 200)`      |
| `clientes_analytics_api` | `"clientes-api/"`                     | `JsonResponse({"ok": False, "stub": "clientes_analytics_api"}, 200)`      |
| `predictive_analytics_api` | `"predictive-api/"`                 | `JsonResponse({"ok": False, "stub": "predictive_analytics_api"}, 200)`   |
| `real_time_metrics_api`   | `"real-time/"`                         | `JsonResponse({"ok": False, "stub": "real_time_metrics_api"}, 200)`       |
| `AIInsightView`      | `"ai-insights/"` (as_view())              | `get()` → `JsonResponse({"ok": False, "stub": "AIInsightView"}, 200)`   |
| `export_report_view` | `"export/"`                               | `JsonResponse({"ok": False, "stub": "export_report_view"}, 200)`         |

En producción, si `AIReportEngine` u otras dependencias fallan, estas vistas pueden reemplazarse por stubs que sigan la tabla anterior.

---

## 4. Cómo aplicar stubs (pasos)

1. **Localizar la vista** que falla (log, `manage.py check`, `resolve()`).
2. **Comprobar la firma** en `urls.py` (args, `as_view()`, `@require_GET`, etc.).
3. **Sustituir el cuerpo** de la vista (o añadir una implementación nueva al final del módulo con el mismo nombre si se quiere conservar el código original comentado) por:
   - `*args, **kwargs` si la URL puede pasar argumentos.
   - `return JsonResponse(...)` o `HttpResponse(...)` con `status=200`.
4. **Añadir el comentario** de stub (ver 2.5).
5. **Reiniciar** el servidor de app (gunicorn/uwsgi, etc.) y comprobar que `manage.py check` y `resolve()` pasan.

---

## 5. Archivos de referencia

- `scripts/STUBS_ANALYTICS_VIEWS.py` — Bloque de stubs para `taller/analytics/views.py` (copiar/pegar).
- `scripts/INSTRUCCIONES_FIX_ANALYTICS_VIEWS.md` — Pasos para aplicar stubs de analytics en el servidor.
- `scripts/fix_analytics_views_stubs.sh` — Script para inyectar stubs en `analytics/views.py`.
- `taller/analytics/views.py` — Donde se aplican (o se han aplicado) stubs de analytics.

---

## 6. Qué evitar

- **Eliminar rutas de `urls.py`** solo para esconder el error: rompe enlaces, redirects y posiblemente el `reverse()` de otras partes.
- **Devolver 500 o 404 en stubs** sin motivo: el objetivo es evitar caídas, no simular fallos.
- **Stubear vistas de login, signup o flujos críticos de negocio** sin plan claro: los stubs deben usarse en análisis, reportes o funcionalidades no críticas; para auth es mejor corregir la vista o desactivar la ruta de forma controlada.
- **Dejar stubs indefinidamente** sin anotar: en el código, ticket o doc se debe indicar que es temporal y cuál es la vista/feature real a restaurar.
