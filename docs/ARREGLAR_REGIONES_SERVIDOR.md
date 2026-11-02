# Arreglar regiones y catálogos Chile en servidor

## 1. Marcas y modelos vacíos (crear vehículo)

Si en `/cl/es/vehiculos/crear/` no aparecen marcas ni modelos en los desplegables:

```bash
python manage.py cargar_marcas_modelos_por_pais --country CL
```

Esto carga ~20 marcas y sus modelos para Chile. Luego reiniciar Gunicorn.

## 2. Conflicto de migraciones

Si aparece:
```
CommandError: Conflicting migrations detected; multiple leaf nodes in the migration graph
```

Ejecutar en el servidor:
```bash
cd /srv/egarage
source venv/bin/activate  # o: source .venv/bin/activate
python manage.py makemigrations --merge
# Cuando pregunte el nombre, presionar Enter para aceptar el default
python manage.py migrate
```

Luego hacer commit de la migración merge generada (ej. `0092_merge_....py`) y desplegar.

## 3. Cargar regiones (sin archivo JSON)

Si `data/regiones_ciudades.json` no existe en el servidor, el comando ahora usa datos embebidos:

```bash
python manage.py cargar_regiones_ciudades
```

Debería mostrar: `OK: X regiones y Y ciudades cargadas.`

## 4. Reiniciar Gunicorn

```bash
sudo systemctl restart gunicorn
```
