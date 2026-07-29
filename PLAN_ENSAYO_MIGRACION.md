# PLAN ENSAYO MIGRACIÓN — VehiculoDesarme
Generado: 2026-06-24
Propósito: ensayar el Escenario A (reordenamiento del libro de migraciones +
creación real de taller_vehiculodesarme) contra una copia clonada de producción.

## Prerequisitos confirmados
- Espacio libre en servidor: 11 GB disponibles
- Tamaño de egarage_db: 24 MB
- gunicorn.service: DJANGO_SETTINGS_MODULE=gestion_taller.settings_prod hardcodeado
  → gunicorn nunca usará settings_ensayo aunque se reinicie durante el ensayo
- taller_vehiculodesarme: NO existe en producción (tabla física ausente, pese a
  que 0077 y 0078 figuran como aplicadas en django_migrations)
- Migraciones 0079–0139: no contienen ninguna referencia a VehiculoDesarme
  (verificado con grep en toda la carpeta migrations/)

---

## ARCHIVO: gestion_taller/settings_ensayo.py
Crear este archivo en el servidor (o comitearlo y hacer pull) antes de comenzar:

```python
# gestion_taller/settings_ensayo.py
# Solo para ensayo de migración — NO usar en producción real.
from .settings_prod import *  # noqa: F401, F403

# Sobrescribir únicamente el nombre de la base.
# Todo lo demás (ENGINE, USER, PASSWORD, HOST, PORT) viene de settings_prod.
DATABASES["default"]["NAME"] = "egarage_db_ensayo"
```

Verifica que el archivo existe:

```bash
ls -la /srv/egarage/gestion_taller/settings_ensayo.py
```

---

## FASE 0 — Preparación (sin tocar la DB de producción)

### Paso 0.1 — Ir al directorio del proyecto y activar venv

```bash
cd /srv/egarage
source venv/bin/activate
```

### Paso 0.2 — Extraer la contraseña de Postgres desde Django (nunca la escribas a mano)

```bash
export PGPASSWORD=$(
  DJANGO_SETTINGS_MODULE=gestion_taller.settings_prod \
  python manage.py shell -c \
  "from django.conf import settings; print(settings.DATABASES['default']['PASSWORD'])"
)
```

Verifica que la variable quedó cargada (debe mostrar algo, no vacío):

```bash
echo "PGPASSWORD cargado: $(echo $PGPASSWORD | wc -c) caracteres"
```

### Paso 0.3 — Crear la base de ensayo

```bash
PGPASSWORD=$PGPASSWORD psql -h 127.0.0.1 -U egarage -d postgres \
  -c "CREATE DATABASE egarage_db_ensayo OWNER egarage;"
```

Si el usuario `egarage` no tiene permiso CREATEDB, usar el superusuario:

```bash
sudo -u postgres psql -c "CREATE DATABASE egarage_db_ensayo OWNER egarage;"
```

### Paso 0.4 — Clonar producción al ensayo con pg_dump

```bash
DUMP_FILE="/tmp/ensayo_$(date +%Y%m%d_%H%M).dump"

pg_dump \
  -h 127.0.0.1 \
  -U egarage \
  -d egarage_db \
  --no-owner --no-privileges \
  -Fc \
  -f "$DUMP_FILE"

echo "Dump guardado en: $DUMP_FILE"
ls -lh "$DUMP_FILE"
```

### Paso 0.5 — Restaurar el dump en egarage_db_ensayo

```bash
pg_restore \
  -h 127.0.0.1 \
  -U egarage \
  -d egarage_db_ensayo \
  --no-owner --no-privileges \
  "$DUMP_FILE"
```

### Paso 0.6 — Verificar que el clon es correcto

```bash
PGPASSWORD=$PGPASSWORD psql -h 127.0.0.1 -U egarage -d egarage_db_ensayo -c "
SELECT
  (SELECT COUNT(*) FROM taller_vehiculo WHERE tipo_uso='DESARME') AS vehiculos_desarme,
  (SELECT COUNT(*) FROM taller_empresa)                           AS empresas,
  (SELECT COUNT(*) FROM taller_piezadesarme)                     AS piezas,
  (SELECT COUNT(*) FROM django_migrations WHERE app='taller')    AS migraciones_taller;
"
```

Los números deben coincidir con producción. Si algo está en 0 cuando no debería, detener.

También confirmar el estado del libro de migraciones respecto a 0077 y 0078:

```bash
PGPASSWORD=$PGPASSWORD psql -h 127.0.0.1 -U egarage -d egarage_db_ensayo -c "
SELECT name, applied
FROM django_migrations
WHERE app = 'taller' AND name IN (
  '0076_empresa_is_trial_restore',
  '0077_vehiculodesarme',
  '0078_migrate_vehiculo_desarme_to_vehiculodesarme',
  '0139_alter_sugerenciapiezadesarme_id'
)
ORDER BY name;
"
```

Esperado: 0076, 0077, 0078, 0139 aparecen como applied. 0140 NO aparece (aún no fue aplicada).

---

## VERIFICACIÓN ESTÁNDAR — correr ANTES de cada paso del Escenario A

Dos chequeos obligatorios. Ambos deben mostrar `egarage_db_ensayo`. Si cualquiera
muestra `egarage_db`, DETENER INMEDIATAMENTE — estás apuntando a producción real.

```bash
# Check 1: lo que Django cree
DJANGO_SETTINGS_MODULE=gestion_taller.settings_ensayo \
  python manage.py shell -c \
  "from django.conf import settings; print('Django NAME:', settings.DATABASES['default']['NAME'])"

# Check 2: lo que Postgres confirma (ground truth)
DJANGO_SETTINGS_MODULE=gestion_taller.settings_ensayo \
  python manage.py dbshell -- -c "SELECT current_database();"
```

Ambos deben responder `egarage_db_ensayo`. Continuar solo si los dos coinciden.

---

## ESCENARIO A — Los 6 pasos (contra egarage_db_ensayo)

### PASO 1 — Desmarcar 0077–0139 del libro (sin tocar la DB física)

```bash
# VERIFICAR BASE ANTES
DJANGO_SETTINGS_MODULE=gestion_taller.settings_ensayo python manage.py shell -c \
  "from django.conf import settings; print('Django NAME:', settings.DATABASES['default']['NAME'])"
DJANGO_SETTINGS_MODULE=gestion_taller.settings_ensayo python manage.py dbshell -- -c "SELECT current_database();"

# EJECUTAR
DJANGO_SETTINGS_MODULE=gestion_taller.settings_ensayo \
  python manage.py migrate taller 0076 --fake
```

Esperado: Django imprime que está "unapplying" (falso) desde la migración actual hasta 0077.
La tabla taller_vehiculodesarme NO cambia (no existe y sigue sin existir).
Las tablas de los otros modelos (taller_vehiculo, taller_piezadesarme, etc.) NO cambian.

### PASO 2 — Crear la tabla de verdad (0077 real, sin --fake)

```bash
# VERIFICAR BASE ANTES
DJANGO_SETTINGS_MODULE=gestion_taller.settings_ensayo python manage.py shell -c \
  "from django.conf import settings; print('Django NAME:', settings.DATABASES['default']['NAME'])"
DJANGO_SETTINGS_MODULE=gestion_taller.settings_ensayo python manage.py dbshell -- -c "SELECT current_database();"

# EJECUTAR
DJANGO_SETTINGS_MODULE=gestion_taller.settings_ensayo \
  python manage.py migrate taller 0077
```

Esperado: Django crea taller_vehiculodesarme con los campos originales (los 17 de 0077).
Verificar que la tabla existe:

```bash
DJANGO_SETTINGS_MODULE=gestion_taller.settings_ensayo \
  python manage.py dbshell -- -c "\d taller_vehiculodesarme"
```

### PASO 3 — Saltar la data migration vieja 0078 (--fake)

```bash
# VERIFICAR BASE ANTES
DJANGO_SETTINGS_MODULE=gestion_taller.settings_ensayo python manage.py shell -c \
  "from django.conf import settings; print('Django NAME:', settings.DATABASES['default']['NAME'])"
DJANGO_SETTINGS_MODULE=gestion_taller.settings_ensayo python manage.py dbshell -- -c "SELECT current_database();"

# EJECUTAR
DJANGO_SETTINGS_MODULE=gestion_taller.settings_ensayo \
  python manage.py migrate taller 0078 --fake
```

Esperado: Django marca 0078 como aplicada sin copiar ningún dato.
taller_vehiculodesarme queda vacía (COUNT = 0).

Verificar:

```bash
DJANGO_SETTINGS_MODULE=gestion_taller.settings_ensayo \
  python manage.py dbshell -- -c "SELECT COUNT(*) FROM taller_vehiculodesarme;"
```

Debe dar 0.

### PASO 4 — Re-registrar 0079–0139 como aplicadas (--fake, no tocan la DB)

```bash
# VERIFICAR BASE ANTES
DJANGO_SETTINGS_MODULE=gestion_taller.settings_ensayo python manage.py shell -c \
  "from django.conf import settings; print('Django NAME:', settings.DATABASES['default']['NAME'])"
DJANGO_SETTINGS_MODULE=gestion_taller.settings_ensayo python manage.py dbshell -- -c "SELECT current_database();"

# EJECUTAR
DJANGO_SETTINGS_MODULE=gestion_taller.settings_ensayo \
  python manage.py migrate taller 0139 --fake
```

Esperado: Django registra todas las migraciones desde 0079 hasta 0139 como aplicadas,
sin ejecutar ningún SQL (ya estaban en la DB clonada).

Verificar que el libro está íntegro:

```bash
DJANGO_SETTINGS_MODULE=gestion_taller.settings_ensayo \
  python manage.py showmigrations taller | tail -20
```

Todas las migraciones hasta 0139 deben aparecer con [X]. La 0140 debe aparecer con [ ].

### PASO 5 — Agregar los 7 campos nuevos (0140 real, sin --fake)

```bash
# VERIFICAR BASE ANTES
DJANGO_SETTINGS_MODULE=gestion_taller.settings_ensayo python manage.py shell -c \
  "from django.conf import settings; print('Django NAME:', settings.DATABASES['default']['NAME'])"
DJANGO_SETTINGS_MODULE=gestion_taller.settings_ensayo python manage.py dbshell -- -c "SELECT current_database();"

# EJECUTAR
DJANGO_SETTINGS_MODULE=gestion_taller.settings_ensayo \
  python manage.py migrate taller 0140
```

Esperado: Django corre 7 ALTER TABLE ADD COLUMN sobre taller_vehiculodesarme.
Verificar que los 7 campos nuevos existen:

```bash
DJANGO_SETTINGS_MODULE=gestion_taller.settings_ensayo \
  python manage.py dbshell -- -c "\d taller_vehiculodesarme"
```

Deben aparecer: es_placeholder, tipo_carroceria, precio_compra, monto_chatarra,
transporte_grua_desarme, otros_gastos_desarme, vendedor_desarme_id.

### PASO 6 — Data migration 0141 (pendiente de escritura)

⚠️  Este paso requiere que 0141 sea escrita y revisada en una sesión separada
antes de correrla aquí. El contenido de 0141 ya está acordado:
  - Copia Vehiculo(tipo_uso='DESARME') → VehiculoDesarme con ID explícito
  - Incluye los 7 campos nuevos que 0078 no copió
  - Es idempotente (salta filas con vehiculo_origen_id ya existente)
  - Incluye SELECT setval(...) para resetear la secuencia de Postgres
  - Tiene backwards() que borra filas con vehiculo_origen_id IS NOT NULL

Cuando 0141 esté lista y aprobada:

```bash
# VERIFICAR BASE ANTES
DJANGO_SETTINGS_MODULE=gestion_taller.settings_ensayo python manage.py shell -c \
  "from django.conf import settings; print('Django NAME:', settings.DATABASES['default']['NAME'])"
DJANGO_SETTINGS_MODULE=gestion_taller.settings_ensayo python manage.py dbshell -- -c "SELECT current_database();"

# EJECUTAR
DJANGO_SETTINGS_MODULE=gestion_taller.settings_ensayo \
  python manage.py migrate taller 0141
```

Verificar que los datos se copiaron:

```bash
DJANGO_SETTINGS_MODULE=gestion_taller.settings_ensayo \
  python manage.py dbshell -- -c "
SELECT
  COUNT(*)                                  AS total_copiados,
  COUNT(*) FILTER (WHERE es_placeholder)    AS placeholders,
  COUNT(*) FILTER (WHERE NOT es_placeholder) AS reales,
  MIN(id)                                   AS id_min,
  MAX(id)                                   AS id_max
FROM taller_vehiculodesarme;
"
```

El total debe coincidir con el COUNT de taller_vehiculo WHERE tipo_uso='DESARME'.

Verificar que la secuencia quedó correcta (el próximo INSERT no colisionará):

```bash
DJANGO_SETTINGS_MODULE=gestion_taller.settings_ensayo \
  python manage.py dbshell -- -c "
SELECT last_value FROM taller_vehiculodesarme_id_seq;
"
```

Debe ser >= MAX(id) de la tabla.

---

## VERIFICACIÓN FINAL DEL ENSAYO

Confirmar que el sistema Django arranca limpio contra el ensayo:

```bash
DJANGO_SETTINGS_MODULE=gestion_taller.settings_ensayo \
  python manage.py check --database default
```

Confirmar que no quedan migraciones pendientes:

```bash
DJANGO_SETTINGS_MODULE=gestion_taller.settings_ensayo \
  python manage.py migrate --check
```

Debe terminar con exit code 0 (sin migraciones pendientes).

---

## LIMPIEZA POST-ENSAYO

Correr solo cuando el ensayo esté completo y validado:

```bash
# 1. Borrar la base de ensayo
sudo -u postgres psql -c "DROP DATABASE egarage_db_ensayo;"

# 2. Borrar el dump de /tmp
rm -f /tmp/ensayo_*.dump

# 3. Borrar el archivo settings_ensayo.py (si se decidió no mantenerlo)
# rm /srv/egarage/gestion_taller/settings_ensayo.py

# 4. Limpiar la variable PGPASSWORD de la sesión
unset PGPASSWORD
```

Nota: settings_ensayo.py puede mantenerse en el repo — no tiene ningún efecto
en producción porque gunicorn tiene settings_prod hardcodeado en su .service.
Es útil para futuras pruebas contra clones.

---

## NOTAS DE SEGURIDAD

1. DJANGO_SETTINGS_MODULE=gestion_taller.settings_ensayo debe estar presente
   en CADA comando manage.py del Escenario A. Si se omite, el comando usará
   el settings que tenga en el entorno de la shell, que podría ser settings_prod.

2. La doble verificación (Django shell + dbshell SELECT current_database()) es
   obligatoria antes de cada paso. Una verificación sola no es suficiente:
   Django puede creer que apunta al ensayo mientras psql está conectando a otro
   lado (no debería pasar, pero la verificación doble lo garantiza).

3. gunicorn NO se toca durante el ensayo. El servicio real sigue corriendo
   contra egarage_db (producción) durante todo el ensayo. Los usuarios no ven
   ningún downtime.

4. Si cualquier paso falla, detener y evaluar. No intentar continuar desde un
   estado intermedio sin entender exactamente qué pasó.

5. El PGPASSWORD exportado en el Paso 0.2 vive solo en la sesión de terminal
   actual. Si abres una nueva terminal para el ensayo, repite el Paso 0.2.
