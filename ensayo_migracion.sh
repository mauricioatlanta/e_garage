#!/usr/bin/env bash
# =============================================================================
# ensayo_migracion.sh
# Ensaya la cirugía de migraciones VehiculoDesarme contra egarage_db_ensayo.
# NO toca egarage_db (producción) en ningún paso.
#
# Prerequisito: gestion_taller/settings_ensayo.py debe existir en el servidor.
# Uso: bash ensayo_migracion.sh
# =============================================================================

set -euo pipefail

# -----------------------------------------------------------------------------
# CONFIGURACIÓN
# -----------------------------------------------------------------------------
APP_DIR="/srv/egarage"
SETTINGS_PROD="gestion_taller.settings_prod"
SETTINGS_ENSAYO="gestion_taller.settings_ensayo"
EXPECTED_DB="egarage_db_ensayo"
LOG_FILE="${APP_DIR}/ensayo_migracion_$(date +%Y%m%d_%H%M).log"
DUMP_FILE="/tmp/ensayo_$(date +%Y%m%d_%H%M).dump"

# Redirigir todo output (stdout + stderr) a pantalla y log simultáneamente.
exec > >(tee -a "$LOG_FILE") 2>&1

echo "============================================================"
echo "  ENSAYO MIGRACIÓN VehiculoDesarme"
echo "  Log: $LOG_FILE"
echo "  Inicio: $(date)"
echo "============================================================"

# -----------------------------------------------------------------------------
# HELPER: verificación doble antes de cada paso del Escenario A.
# Recibe el label del paso como argumento.
# Aborta si Django o Postgres no dicen exactamente "egarage_db_ensayo".
# -----------------------------------------------------------------------------
verify_db() {
    local label="$1"
    echo ""
    echo "  [VERIFY] ${label} — verificando base activa..."

    # Check 1: lo que Django cree según su settings
    local django_name
    django_name=$(
        DJANGO_SETTINGS_MODULE="$SETTINGS_ENSAYO" \
        python manage.py shell -c \
        "from django.conf import settings; print(settings.DATABASES['default']['NAME'])" \
        2>/dev/null | tr -d ' \n\r'
    )
    if [[ "$django_name" != "$EXPECTED_DB" ]]; then
        echo ""
        echo "  !! ABORT: Django NAME='${django_name}' — se esperaba '${EXPECTED_DB}'"
        echo "  !! El script apuntaría a la base equivocada. Deteniendo."
        exit 1
    fi
    echo "  [OK] Django NAME: ${django_name}"

    # Check 2: lo que Postgres confirma (ground truth)
    local pg_name
    pg_name=$(
        DJANGO_SETTINGS_MODULE="$SETTINGS_ENSAYO" \
        python manage.py dbshell -- -t -c "SELECT current_database();" \
        2>/dev/null | tr -d ' \n\r'
    )
    if [[ "$pg_name" != "$EXPECTED_DB" ]]; then
        echo ""
        echo "  !! ABORT: Postgres current_database()='${pg_name}' — se esperaba '${EXPECTED_DB}'"
        echo "  !! Postgres y Django no coinciden o apuntan a la base equivocada. Deteniendo."
        exit 1
    fi
    echo "  [OK] Postgres current_database(): ${pg_name}"
}

# =============================================================================
# FASE 0 — PREPARACIÓN
# =============================================================================
echo ""
echo "============================================================"
echo "FASE 0 — PREPARACIÓN"
echo "============================================================"

# ---- 0.1 ----
echo ""
echo "[0.1] Directorio y venv"
cd "$APP_DIR"
source venv/bin/activate
echo "  [OK] Directorio: $(pwd)"
echo "  [OK] Python: $(which python)"

# ---- 0.2 ----
echo ""
echo "[0.2] Extraer conexión Postgres desde Django (sin escribir credenciales a mano)"

export PGPASSWORD
PGPASSWORD=$(
    DJANGO_SETTINGS_MODULE="$SETTINGS_PROD" \
    python manage.py shell -c \
    "from django.conf import settings; print(settings.DATABASES['default']['PASSWORD'])" \
    2>/dev/null | tr -d ' \n\r'
)
if [[ -z "$PGPASSWORD" ]]; then
    echo "  !! ABORT: PGPASSWORD vacío — revisa DJANGO_DB_PASSWORD en .env.prod"
    exit 1
fi
echo "  [OK] PGPASSWORD cargado ($(printf '%s' "$PGPASSWORD" | wc -c) caracteres)"

PG_HOST=$(
    DJANGO_SETTINGS_MODULE="$SETTINGS_PROD" \
    python manage.py shell -c \
    "from django.conf import settings; print(settings.DATABASES['default']['HOST'])" \
    2>/dev/null | tr -d ' \n\r'
)
PG_USER=$(
    DJANGO_SETTINGS_MODULE="$SETTINGS_PROD" \
    python manage.py shell -c \
    "from django.conf import settings; print(settings.DATABASES['default']['USER'])" \
    2>/dev/null | tr -d ' \n\r'
)
PG_SOURCE_DB=$(
    DJANGO_SETTINGS_MODULE="$SETTINGS_PROD" \
    python manage.py shell -c \
    "from django.conf import settings; print(settings.DATABASES['default']['NAME'])" \
    2>/dev/null | tr -d ' \n\r'
)
echo "  [OK] Host: ${PG_HOST} | User: ${PG_USER} | DB origen: ${PG_SOURCE_DB}"

# Guardia: el origen no puede ser el mismo que el destino
if [[ "$PG_SOURCE_DB" == "$EXPECTED_DB" ]]; then
    echo "  !! ABORT: settings_prod apunta a '${PG_SOURCE_DB}', que coincide con el destino."
    echo "  !! settings_prod debe apuntar a la base de producción real, no al ensayo."
    exit 1
fi

# ---- 0.3 ----
echo ""
echo "[0.3] Crear base de ensayo: ${EXPECTED_DB}"
ALREADY_EXISTS=$(
    psql -h "$PG_HOST" -U "$PG_USER" -d postgres -t \
    -c "SELECT COUNT(*) FROM pg_database WHERE datname='${EXPECTED_DB}';" \
    | tr -d ' \n\r'
)
if [[ "$ALREADY_EXISTS" == "1" ]]; then
    echo "  [!] La base '${EXPECTED_DB}' ya existe."
    echo "  [!] Si tiene datos viejos de un ensayo anterior, descárgala primero:"
    echo "  [!]   sudo -u postgres psql -c \"DROP DATABASE ${EXPECTED_DB};\""
    read -r -p "  ¿Continuar con la base existente? [s/N] " CONT_EXISTING
    if [[ "$CONT_EXISTING" != "s" && "$CONT_EXISTING" != "S" ]]; then
        echo "  Abortando por confirmación del usuario."
        exit 1
    fi
else
    psql -h "$PG_HOST" -U "$PG_USER" -d postgres \
        -c "CREATE DATABASE ${EXPECTED_DB} OWNER ${PG_USER};"
    echo "  [OK] Base '${EXPECTED_DB}' creada"
fi

# ---- 0.4 ----
echo ""
echo "[0.4] pg_dump de producción: ${PG_SOURCE_DB} → ${DUMP_FILE}"
pg_dump \
    -h "$PG_HOST" \
    -U "$PG_USER" \
    -d "$PG_SOURCE_DB" \
    --no-owner --no-privileges \
    -Fc \
    -f "$DUMP_FILE"
echo "  [OK] Dump creado: $(ls -lh "$DUMP_FILE" | awk '{print $5, $NF}')"

# ---- 0.5 ----
echo ""
echo "[0.5] pg_restore → ${EXPECTED_DB}"
pg_restore \
    -h "$PG_HOST" \
    -U "$PG_USER" \
    -d "$EXPECTED_DB" \
    --no-owner --no-privileges \
    "$DUMP_FILE"
echo "  [OK] Restore completado"

# ---- 0.6 ----
echo ""
echo "[0.6] Verificar integridad del clon"
psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -c "
SELECT
  (SELECT COUNT(*) FROM taller_vehiculo WHERE tipo_uso='DESARME') AS vehiculos_desarme,
  (SELECT COUNT(*) FROM taller_empresa)                           AS empresas,
  (SELECT COUNT(*) FROM taller_piezadesarme)                     AS piezas,
  (SELECT COUNT(*) FROM django_migrations WHERE app='taller')    AS migraciones_taller;
"
echo ""
psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -c "
SELECT name, applied
FROM django_migrations
WHERE app='taller'
  AND name IN (
    '0076_empresa_is_trial_restore',
    '0077_vehiculodesarme',
    '0078_migrate_vehiculo_desarme_to_vehiculodesarme',
    '0139_alter_sugerenciapiezadesarme_id'
  )
ORDER BY name;
"
echo "  Esperado: 0076, 0077, 0078, 0139 como applied; 0140 ausente."
echo ""
read -r -p "  ¿Los números coinciden con producción y el libro se ve correcto? [s/N] " CONFIRM
if [[ "$CONFIRM" != "s" && "$CONFIRM" != "S" ]]; then
    echo "  Abortando por confirmación del usuario."
    exit 1
fi
echo "  [OK] Fase 0 completada — clon listo"

# =============================================================================
# ESCENARIO A — PASOS 1 A 5
# =============================================================================
echo ""
echo "============================================================"
echo "ESCENARIO A — Reordenamiento del libro de migraciones"
echo "============================================================"

# =============================================================================
# PASO 1 — Desmarcar 0077-0139 del libro (--fake a 0076)
# =============================================================================
echo ""
echo "────────────────────────────────────────────────────────────"
echo "[PASO 1/6] Desmarcar 0077-0139 del libro (--fake a 0076, sin SQL en la DB)"
echo "────────────────────────────────────────────────────────────"
verify_db "Paso 1"

DJANGO_SETTINGS_MODULE="$SETTINGS_ENSAYO" \
    python manage.py migrate taller 0076 --fake

echo "  [OK] Paso 1 ejecutado"

# CHECK EXTRA: ningún app fuera de taller debe haber perdido migraciones
echo ""
echo "  [CHECK EXTRA] Verificando que ningún app fuera de 'taller' tiene migraciones desmarcadas..."
DJANGO_SETTINGS_MODULE="$SETTINGS_ENSAYO" python manage.py shell -c "
from django.db.migrations.executor import MigrationExecutor
from django.db import connection

executor = MigrationExecutor(connection)
plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
bad_apps = sorted({m.app_label for m, _ in plan if m.app_label != 'taller'})
if bad_apps:
    print('ERROR: apps con migraciones desmarcadas ademas de taller:', bad_apps)
    raise SystemExit(1)
pending_taller = [m.name for m, _ in plan if m.app_label == 'taller']
print('OK: solo taller tiene migraciones pendientes (' + str(len(pending_taller)) + ')')
print('   Primeras 5:', pending_taller[:5])
"
echo "  [OK] Check extra Paso 1 pasado"

# =============================================================================
# PASO 2 — Crear la tabla taller_vehiculodesarme (0077 real)
# =============================================================================
echo ""
echo "────────────────────────────────────────────────────────────"
echo "[PASO 2/6] Crear tabla taller_vehiculodesarme (0077 real, sin --fake)"
echo "────────────────────────────────────────────────────────────"
verify_db "Paso 2"

DJANGO_SETTINGS_MODULE="$SETTINGS_ENSAYO" \
    python manage.py migrate taller 0077

echo "  [OK] Paso 2 ejecutado"

# CHECK: schema vía psql
echo ""
echo "  [CHECK] Columnas de taller_vehiculodesarme:"
psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -c "\d taller_vehiculodesarme"

# CHECK EXTRA: prueba ORM end-to-end
echo ""
echo "  [CHECK EXTRA] Prueba ORM: VehiculoDesarme.objects.count()..."
DJANGO_SETTINGS_MODULE="$SETTINGS_ENSAYO" python manage.py shell -c "
from taller.models.vehiculo_desarme import VehiculoDesarme
count = VehiculoDesarme.objects.count()
print(f'ORM OK: VehiculoDesarme.objects.count() = {count}')
# Confirmar que el modelo puede acceder a campos nuevos sin error
_ = VehiculoDesarme._meta.get_field('es_placeholder')
print('ORM OK: campo es_placeholder accesible en el meta del modelo')
"
echo "  [OK] Check extra Paso 2 pasado"

# =============================================================================
# PASO 3 — Saltar data migration vieja 0078 (--fake)
# =============================================================================
echo ""
echo "────────────────────────────────────────────────────────────"
echo "[PASO 3/6] Saltar data migration vieja 0078 (--fake, sin copiar datos)"
echo "────────────────────────────────────────────────────────────"
verify_db "Paso 3"

DJANGO_SETTINGS_MODULE="$SETTINGS_ENSAYO" \
    python manage.py migrate taller 0078 --fake

echo "  [OK] Paso 3 ejecutado"

# CHECK: la tabla debe seguir vacía
VDCOUNT=$(
    psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -t \
    -c "SELECT COUNT(*) FROM taller_vehiculodesarme;" \
    | tr -d ' \n\r'
)
if [[ "$VDCOUNT" != "0" ]]; then
    echo "  !! ABORT: taller_vehiculodesarme tiene ${VDCOUNT} filas después de fakear 0078."
    echo "  !! La tabla ya tenía datos en el clon — evaluar manualmente antes de continuar."
    exit 1
fi
echo "  [OK] taller_vehiculodesarme vacía: ${VDCOUNT} filas (correcto)"

# =============================================================================
# PASO 4 — Re-registrar 0079-0136 como aplicadas (--fake)
# Solo hasta 0136, que es el último migration genuinamente en producción.
# 0137-0139 NO se fakean — se aplicarán de verdad en el Paso 5.
# =============================================================================
echo ""
echo "────────────────────────────────────────────────────────────"
echo "[PASO 4/6] Re-registrar 0079-0136 como aplicadas (--fake, sin SQL en la DB)"
echo "────────────────────────────────────────────────────────────"
verify_db "Paso 4"

DJANGO_SETTINGS_MODULE="$SETTINGS_ENSAYO" \
    python manage.py migrate taller 0136 --fake

echo "  [OK] Paso 4 ejecutado"

# CHECK: confirmar que 0137 aparece como pendiente ([ ])
echo ""
echo "  [CHECK] 0136 debe ser [X], 0137 debe ser [ ]:"
DJANGO_SETTINGS_MODULE="$SETTINGS_ENSAYO" \
    python manage.py showmigrations taller | grep -E "013[6-9]|0140"

# =============================================================================
# PASO 5 — Aplicar 0137, 0138, 0139 DE VERDAD (sin --fake)
# Crea la tabla taller_sugerenciapiezadesarme y ajusta tipo_carroceria en Vehiculo.
# =============================================================================
echo ""
echo "────────────────────────────────────────────────────────────"
echo "[PASO 5/6] Aplicar 0137, 0138, 0139 reales (SugerenciaPiezaDesarme + tipo_carroceria)"
echo "────────────────────────────────────────────────────────────"
verify_db "Paso 5"

DJANGO_SETTINGS_MODULE="$SETTINGS_ENSAYO" \
    python manage.py migrate taller 0139

echo "  [OK] Paso 5 ejecutado"

# CHECK: tabla de sugerencias existe y está vacía
echo ""
echo "  [CHECK] taller_sugerenciapiezadesarme debe existir:"
psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -c "\d taller_sugerenciapiezadesarme" | head -10

SPD_COUNT=$(
    psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -t \
    -c "SELECT COUNT(*) FROM taller_sugerenciapiezadesarme;" \
    | tr -d ' \n\r'
)
echo "  [OK] taller_sugerenciapiezadesarme filas: ${SPD_COUNT} (esperado: 0 en ensayo)"

# CHECK: confirmar que tipo_carroceria en taller_vehiculo tiene max_length=20
VEH_MAXLEN=$(
    psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -t -c "
SELECT character_maximum_length
FROM information_schema.columns
WHERE table_name='taller_vehiculo' AND column_name='tipo_carroceria';" \
    | tr -d ' \n\r'
)
if [[ "$VEH_MAXLEN" != "20" ]]; then
    echo "  !! ABORT: taller_vehiculo.tipo_carroceria max_length='${VEH_MAXLEN}' — se esperaba 20"
    exit 1
fi
echo "  [OK] taller_vehiculo.tipo_carroceria max_length=${VEH_MAXLEN}"

# CHECK: libro actualizado
echo ""
echo "  [CHECK] Estado del libro — 0136-0140:"
DJANGO_SETTINGS_MODULE="$SETTINGS_ENSAYO" \
    python manage.py showmigrations taller | grep -E "013[6-9]|0140"

# =============================================================================
# PASO 6 — Agregar los 7 campos nuevos a taller_vehiculodesarme (0140 real)
# =============================================================================
echo ""
echo "────────────────────────────────────────────────────────────"
echo "[PASO 6/6] Agregar 7 campos nuevos a taller_vehiculodesarme (0140 real)"
echo "────────────────────────────────────────────────────────────"
verify_db "Paso 6"

DJANGO_SETTINGS_MODULE="$SETTINGS_ENSAYO" \
    python manage.py migrate taller 0140

echo "  [OK] Paso 6 ejecutado"

# CHECK: schema final
echo ""
echo "  [CHECK] Schema final de taller_vehiculodesarme:"
psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -c "\d taller_vehiculodesarme"

# CHECK: los 7 campos específicos existen
FIELD_COUNT=$(
    psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -t -c "
SELECT COUNT(*) FROM information_schema.columns
WHERE table_name = 'taller_vehiculodesarme'
  AND column_name IN (
    'es_placeholder', 'tipo_carroceria', 'precio_compra',
    'monto_chatarra', 'transporte_grua_desarme',
    'otros_gastos_desarme', 'vendedor_desarme_id'
  );" | tr -d ' \n\r'
)
if [[ "$FIELD_COUNT" != "7" ]]; then
    echo "  !! ABORT: solo ${FIELD_COUNT} de 7 campos nuevos encontrados."
    exit 1
fi
echo "  [OK] Los 7 campos nuevos presentes (${FIELD_COUNT}/7)"

# =============================================================================
# PASO 7 — COMENTADO: 0141 aún no está escrita ni aprobada
# =============================================================================
# Cuando 0141 esté lista, descomentar este bloque completo y volver a correr.
#
# echo ""
# echo "────────────────────────────────────────────────────────────"
# echo "[PASO 7/7] Data migration 0141 — copia Vehiculo DESARME → VehiculoDesarme"
# echo "────────────────────────────────────────────────────────────"
# verify_db "Paso 7"
#
# DJANGO_SETTINGS_MODULE="$SETTINGS_ENSAYO" \
#     python manage.py migrate taller 0141
#
# echo "  [OK] Paso 7 ejecutado"
#
# echo ""
# echo "  [CHECK] Datos copiados y secuencia:"
# psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -c "
# SELECT
#   COUNT(*)                                   AS total_copiados,
#   COUNT(*) FILTER (WHERE es_placeholder)     AS placeholders,
#   COUNT(*) FILTER (WHERE NOT es_placeholder) AS reales,
#   MIN(id) AS id_min,
#   MAX(id) AS id_max
# FROM taller_vehiculodesarme;"
#
# LAST_SEQ=$(psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -t \
#   -c "SELECT last_value FROM taller_vehiculodesarme_id_seq;" | tr -d ' \n\r')
# MAX_ID=$(psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -t \
#   -c "SELECT COALESCE(MAX(id),0) FROM taller_vehiculodesarme;" | tr -d ' \n\r')
# if [[ "$LAST_SEQ" -lt "$MAX_ID" ]]; then
#     echo "  !! ABORT: secuencia (${LAST_SEQ}) < MAX(id) (${MAX_ID}) — riesgo de colisión de IDs"
#     exit 1
# fi
# echo "  [OK] Secuencia OK: last_value=${LAST_SEQ}, MAX(id)=${MAX_ID}"

# =============================================================================
# VERIFICACIÓN FINAL
# =============================================================================
echo ""
echo "============================================================"
echo "VERIFICACIÓN FINAL"
echo "============================================================"

echo ""
echo "[FINAL 1] manage.py check --database default"
DJANGO_SETTINGS_MODULE="$SETTINGS_ENSAYO" \
    python manage.py check --database default
echo "  [OK] system check pasado"

echo ""
echo "[FINAL 2] manage.py migrate --check"
# Mientras 0141 no exista, no debe haber nada pendiente.
# Si 0141 ya fue creada pero no aplicada, --check saldrá con error (esperado).
if DJANGO_SETTINGS_MODULE="$SETTINGS_ENSAYO" python manage.py migrate --check 2>&1; then
    echo "  [OK] No hay migraciones pendientes"
else
    echo "  [!] Hay migraciones pendientes — lista:"
    DJANGO_SETTINGS_MODULE="$SETTINGS_ENSAYO" \
        python manage.py showmigrations taller | grep "\[ \]" || true
    echo "  [!] Si la única pendiente es 0141, esto es correcto — aún no se aplica."
fi

echo ""
echo "============================================================"
echo "  ENSAYO COMPLETADO — Fase 0 + Pasos 1 a 6 OK"
echo "  Paso 7 (0141) pendiente de escritura y aprobación"
echo "  Log completo en: $LOG_FILE"
echo "  Fin: $(date)"
echo "============================================================"
echo ""
echo "LIMPIEZA (correr manualmente cuando lo decidas):"
echo "  sudo -u postgres psql -c \"DROP DATABASE ${EXPECTED_DB};\""
echo "  rm -f ${DUMP_FILE}"
echo "  # rm ${APP_DIR}/gestion_taller/settings_ensayo.py   (opcional)"
echo "  unset PGPASSWORD"
