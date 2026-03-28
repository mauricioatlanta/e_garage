# Cadena de templates — formulario de documentos USA

## Vista efectiva (producción)

`DocumentoCreateView` y `DocumentoUpdateView` (`taller/documentos/views_migrated.py`) usan:

```python
base_template_name = "documentos/document_form.html"
```

`CountryLangTemplateMixin` + `select_country_lang_template()` resuelven por orden; para **US** los candidatos relevantes incluyen:

1. `taller/us/en/documentos/document_form.html` — si la URL/idioma es EN  
2. `taller/us/es/documentos/document_form.html` — si es ES  
3. `taller/us/documentos/document_form.html` — fallback por país  
4. … hasta `taller/common/documentos/document_form.html`

## Cadena oficial (futurista USA)

| Archivo | Rol |
|--------|-----|
| `templates/taller/us/en/documentos/document_form.html` | Primera opción US+EN; extiende la capa intermedia. |
| `templates/taller/us/es/documentos/document_form.html` | Primera opción US+ES; extiende la capa intermedia. |
| `templates/taller/us/documentos/document_form.html` | Capa intermedia: `extra_css`, `us_document_form_futurist.css`, clase `eg-us-doc-form-futurist`, fuentes. Extiende `taller/common/documentos/document_form.html`. |

## Templates legacy (`templates/us/...`)

Siguen existiendo para **fallbacks** (p. ej. `select_template` en vistas country-aware que prueban `us/{lang}/documentos/crear_documento.html` o `editar_documento.html`).

**Regla:** deben hacer `{% extends "taller/us/documentos/document_form.html" %}` para no romper el look USA ni generar “doble verdad” con el common.

Archivos:

- `templates/us/en/documentos/crear_documento.html`
- `templates/us/es/documentos/crear_documento.html`
- `templates/us/en/documentos/editar_documento.html`
- `templates/us/es/documentos/editar_documento.html`

## Qué no usar como fuente de verdad

- Carpetas espejo fuera de `TEMPLATES['DIRS']` (p. ej. copias bajo `deploy_*`) si el despliegue real solo monta `templates/` del repo.

## Verificación rápida en HTML

Con sesión autenticada USA, el documento debería incluir referencias a:

- `us_document_form_futurist.css`
- clase en `<html>`: `eg-us-doc-form-futurist`
- Google Fonts (Exo 2 / Orbitron / Share Tech Mono)

## Nota de diseño (compacto USA)

El tema futurista prioriza **columna más angosta** (`#doc-shell` con `max-width` ~52rem), no **aplastar la altura** de inputs. Las variables `--doc-input-h` / `--doc-input-fs` deben alinearse al formulario común (~34px / 14px).
