# Corrección de botones del Workspace (500 / 404)

## Causas corregidas

1. **Error 500 en Vehicles y Documents**
   - **Template inexistente**: `DocumentoListView` forzaba `taller/us/en/documentos/lista_documentos.html` pero en el proyecto el archivo está en `us/en/documentos/lista_documentos.html`. Se añadieron fallbacks en orden.
   - **Acceso a `empresa`**: En `CountryLangTemplateMixin` y en vistas se usaba `request.user.empresa`; si el usuario no tiene empresa (OneToOne) Django lanza `ObjectDoesNotExist` → 500. Se sustituyó por acceso con `try/except` en mixin, documentos y desarme.
   - **Prints de depuración**: Se quitaron los `print()` del mixin que podían afectar la respuesta.

2. **Error 404 en Disassembly**
   - Cuando el módulo desarme no carga (`ImportError`), solo existía la ruta `""`, por lo que `/us/en/desarme/vehiculos/` no coincidía. Se añadieron rutas de fallback en `urls_desarme.py` y la plantilla `unavailable.html`.

3. **Enlaces del workspace**
   - Para US, los botones usan ahora rutas de nivel raíz: `/us/vehiculos/`, `/us/documentos/`, `/us/en/desarme/`, que están registradas explícitamente en `gestion_taller/urls.py`.

## Archivos modificados

- `taller/views_ingreso.py`: URLs de botones para US con rutas raíz.
- `taller/documentos/views_migrated.py`: `_get_empresa_safe`, fallbacks de template para US, uso seguro de empresa en list/detail/delete.
- `taller/mixins.py`: Obtención segura de `empresa` y eliminación de prints en `CountryLangTemplateMixin`.
- `taller/vehiculos/views_fbv.py`: `_get_empresa_safe`, más fallbacks de template en lista.
- `taller/desarme/views.py`: `_empresa_or_redirect` con acceso seguro a empresa.
- `taller/urls_desarme.py`: Fallback para `vehiculos/` y `<path:subpath>` cuando hay `ImportError`.
- `templates/taller/desarme/unavailable.html`: Página cuando el módulo desarme no está disponible.

## Cómo desplegar y comprobar

1. **Subir los cambios al servidor** (git pull o copia de archivos).

2. **Reiniciar la aplicación** para cargar el código nuevo:
   ```bash
   sudo systemctl restart gunicorn
   # o el comando que use tu despliegue
   ```

3. **Probar en el navegador** (sin caché o en ventana privada):
   - Entrar a `https://www.egarage.cl/us/en/workspace/`
   - Clic en **Vehicles** → debe ir a lista de vehículos (sin 500).
   - Clic en **Documents** → debe ir a lista de documentos (sin 500).
   - Clic en **Disassembly** → debe ir al módulo desarme o a la página "temporarily unavailable" (no 404).

4. **Si sigue fallando**, revisar logs del servidor:
   ```bash
   sudo journalctl -u gunicorn -n 100 --no-pager
   ```
   Buscar líneas con el traceback del 500 o el 404 para ver la causa concreta (template, import, etc.).
