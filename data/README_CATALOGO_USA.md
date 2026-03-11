# Catálogo USA — CSV e importación

Archivos CSV para el comando `import_modelos_usa`.

## En el servidor

1. **Aplicar migraciones** (necesario para que existan las columnas `anio_desde` / `anio_hasta`):

   ```bash
   cd /srv/egarage
   source venv/bin/activate
   python manage.py migrate
   ```

   Si aparece "Conflicting migrations detected; multiple leaf nodes", el repo debería incluir ya una migración de merge que una las hojas (p. ej. `0091_merge_0090_and_0087_merge`). Haz pull de los últimos cambios y vuelve a ejecutar `python manage.py migrate`. Si el conflicto persiste, ejecuta una sola vez:

   ```bash
   python manage.py makemigrations --merge --noinput
   python manage.py migrate
   ```

   y sube la nueva migración de merge generada al repo.

2. **Ruta al CSV**: el argumento `--csv` es relativo al directorio desde el que ejecutas `manage.py`. Si ejecutas desde `/srv/egarage`:

   - `data/catalogo_usa_anual_ejemplo.csv` → busca `/srv/egarage/data/catalogo_usa_anual_ejemplo.csv`
   - Si `data/` no existe o no está desplegada, usa ruta absoluta:  
     `--csv /ruta/completa/al/archivo.csv`

3. **Ejemplo de uso** (con archivos en `data/`):

   ```bash
   python manage.py import_modelos_usa --csv data/catalogo_usa_anual_ejemplo.csv --dry-run
   python manage.py import_modelos_usa --csv data/catalogo_usa_anual_ejemplo.csv --clear
   ```

## Archivos de ejemplo en este repo

- `catalogo_usa_anual_ejemplo.csv` — formato anual (marca, modelo, anio), se consolidan rangos.
- `catalogo_usa_ejemplo.csv` — formato rango (marca, modelo, anio_desde, anio_hasta).

Para carga masiva, genera o sube `catalogo_usa_full.csv` (o varios CSV) y ejecuta con `--clear` para reemplazar el catálogo.
