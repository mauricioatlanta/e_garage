# Fix Settings: guardado de configuración, logo y dominio

**Fecha:** 2026-08-09
**Ruta afectada:** `/cl/es/settings/`
**Estado:** Corregido y validado localmente

## Problema

- El logo podía seleccionarse, pero los cambios no se guardaban.
- El botón **Guardar Configuración** parecía no funcionar.

## Causas raíz

1. `company_settings_views.py` había perdido la lógica general de validación y persistencia de Settings.
2. El panel de usuarios había introducido formularios HTML anidados dentro de `settingsForm`.
3. `DominioPersonalizadoForm.dominio` emitía `required` dentro del formulario global.

Chrome bloqueaba el submit antes de llegar a Django cuando el dominio estaba vacío.

Evidencia obtenida:

- `formValid=false`
- `name=dominio`
- `required=true`
- `SUBMIT_EVENT_SEEN=false`
- `An invalid form control with name='dominio' is not focusable.`

## Solución backend

Archivo: `taller/views_extra/company_settings_views.py`

Se restauró:

- `CompanyProfileForm`
- `FinancialSettingsForm`
- `ThemeSettingsForm`
- `_collect_form_errors()`
- `_sync_company_models()`
- `config.save()`
- sincronización mediante `BrandingService`
- invalidación de caché

Se conservaron usuarios del sistema, técnicos, dominios y suscripción.

El formulario de dominio se renderiza con:

`DominioPersonalizadoForm(use_required_attribute=False)`

La validación backend del dominio continúa siendo obligatoria.

## Solución frontend

Archivo: `templates/taller/company/settings.html`

- Eliminados formularios `<form>` anidados.
- `settingsForm` queda como formulario principal único.
- El logo pertenece correctamente al formulario principal.
- Las acciones de usuarios usan botones submit identificados por nombre/valor.
- El botón `saveBtn` vuelve a realizar el submit normal.

## Validación

- `FORM_STRUCTURE_OK=True`
- `System check identified no issues (0 silenced).`
- `4 passed` en `taller/tests/test_company_settings_view.py`

Prueba funcional real:

- `POST /cl/es/settings/ HTTP/1.1 302`
- `GET /cl/es/settings/ HTTP/1.1 200`
- `GET /media/company_logos/atlantareciclajes.jpg HTTP/1.1 200`

## Base de datos

No hubo cambios de esquema ni migraciones.

## Regla para evitar regresiones

No agregar campos HTML `required` de acciones secundarias dentro de `settingsForm` si no son obligatorios para **Guardar Configuración**.

No utilizar formularios `<form>` anidados.

## Resultado

`/cl/es/settings/` permite nuevamente editar datos de empresa, cambiar y guardar logo, guardar configuración, gestionar usuarios y técnicos, y registrar dominios manteniendo validación backend.
