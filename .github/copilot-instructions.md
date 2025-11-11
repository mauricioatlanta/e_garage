## Objetivo corto
Proveer a los asistentes de IA el contexto mínimo y accionable para trabajar productivamente en este repo Django + frontend React (multi-país / multi-empresa).

## Big picture (rápido)
- Backend: Django (punto de entrada: `manage.py`, settings por defecto `gestion_taller.settings`).
- Frontend: `frontend/` (Create React App). E2E tests en `tests/e2e/` usan Playwright.
- Multi-tenant ligero: cada request se asocia a una `Empresa` (subscriber) vía `request.user.empresa` o middleware (`EmpresaMiddleware`). Ver `ANALISIS_I18N_TEMPLATES.md` y `AJUSTES_VIEWS_FBV.md` para decisiones de routing por país y empresa.

## Qué revisar primero (archivos clave)
- Plantillas de onboarding y landing: `templates/onboarding/bienvenida_usa.html` (ejemplo de uso de `{% load country_url %}` y `{% static 'img/...' %}`).
- Middleware / i18n analysis: `ANALISIS_I18N_TEMPLATES.md` (explica `EmpresaMiddleware` y `SimpleCountryRedirectMiddleware`).
- Seguridad multi-tenant y APIs: `API_DOCUMENTOS_MEJORADA.md` (muestra patrón correcto: `empresa = request.user.empresa`).
- Views y guías para adaptar FBV/CBV: `AJUSTES_VIEWS_FBV.md`.
- Scripts útiles para dev/test: `assign_admin_empresa.py`, `arreglar_taller2.py` (asignar empresa de prueba/crear datos).
- Dependencias: `requirements.txt`.

## Patrones y convenciones específicas
- Multi-tenant safe pattern: nunca confiar en `empresa_id` del payload; usar `request.user.empresa`. Ejemplo (citado):
  - Correcto: `emp = request.user.empresa` (ver `API_DOCUMENTOS_MEJORADA.md`).
  - Usado frecuentemente en views/helpers y en backups (`_backup` scripts importan `Empresa`).
- Obtener alcance en vistas: usar `get_user_scope(request)` o `getattr(request.user, 'empresa', None)` cuando aplique. Revisar `AJUSTES_VIEWS_FBV.md` para ejemplos.
- URLs por país / templates: plantilla usa `{% load country_url %}` y `{% country_url 'namespace:view' %}` para mantener rutas con prefijos de país.
- Recursos estáticos: plantillas usan `{% static 'img/egarage_logo.png' %}` — estática central en `static/img`.

## Comandos frecuentes (dev / test)
- Crear entorno y dependencias:
  - python -m venv .venv
  - .venv\Scripts\Activate (Windows PowerShell: `.\.venv\Scripts\Activate`)
  - pip install -r requirements.txt
- Levantar servidor Django en desarrollo (esperado por e2e):
  - `python manage.py runserver` (expone `http://127.0.0.1:8000`)
- Ejecutar tests frontend / Playwright (ver `tests/e2e/README.md`):
  - `npm install` dentro de `frontend/` o en `tests/e2e` según configuración
  - `npx playwright install`
  - `npm test` o los scripts documentados en `tests/e2e/README.md`

## Errores comunes y dónde mirar
- Problemas de empresa/tenant (logo, lema, name) aparecen si la vista/template no recibe `request.user.empresa` o `request.empresa` correctamente. Buscar:
  - Vistas que usan `Empresa.objects.get(id=...)` o `empresa_id` desde payload (anti-patrón).
  - Templates que renderizan datos globales en vez de los valores por empresa (ej.: `templates/onboarding/bienvenida_usa.html` muestra logos estáticos; poner variables desde la vista si requiere personalización).
- Middleware y contexto: confirmar que `EmpresaMiddleware` está activo si esperas `request.empresa` en plantillas. Ver `ANALISIS_I18N_TEMPLATES.md`.

## Ejemplos concretos de cambios típicos
- Para asegurar logo/lema por empresa en una landing concreta:
  1. En la view que renderiza la página, añadir:
     ```py
     empresa = getattr(request.user, 'empresa', None)
     return render(request, 'onboarding/bienvenida_usa.html', {'empresa': empresa})
     ```
  2. En la plantilla, sustituir los valores estáticos por `{{ empresa.logo.url }}`, `{{ empresa.nombre_taller }}`, `{{ empresa.lema }}` (con checks `if empresa`).

## Seguridad y pruebas rápidas
- Para pruebas rápidas en dev se puede usar `db.sqlite3` incluido y ejecutar `assign_admin_empresa.py` para asignar admin a una empresa de prueba.
- CI: revisar workflow `actions/workflows/django.yml` (badge en `docs/README.md`) para ver cómo se arranca el app en CI.

## Dónde pedir más contexto
- Si falta información sobre cómo se guardan logos/lemas (campo/modelo exacto), busca `taller/models/empresa.py` o pregunta al mantenedor; los scripts de backup (`_backup`) y `assign_admin_empresa.py` muestran los nombres de campos usados (ej. `nombre_taller`).

Si quieres, aplico este borrador como `.github/copilot-instructions.md` y luego lo iteramos — dime si prefieres que incluya ejemplos de cambio de plantilla concretos (patch) o referencias exactas a modelos (`taller/models/empresa.py`).
