#!/usr/bin/env bash
# =============================================================================
# ensayo_migracion_fase2.sh
# Cirugía completa Fase 1 + Fase 2 de migraciones VehiculoDesarme
# contra egarage_db_ensayo (clon ya creado desde producción).
#
# PREREQUISITO: egarage_db_ensayo ya existe, creada por pg_dump/pg_restore
# de egarage_db. Este script NO la crea — solo opera sobre ella.
# El clon debe estar en migración 0136 con el descuadre 0077/0078 intacto.
#
# NO toca egarage_db (producción) en ningún paso.
# Uso: bash ensayo_migracion_fase2.sh
# =============================================================================

set -euo pipefail

# -----------------------------------------------------------------------------
# CONFIGURACIÓN
# -----------------------------------------------------------------------------
APP_DIR="/srv/egarage_ensayo"
SETTINGS_PROD="gestion_taller.settings_prod"
SETTINGS_ENSAYO="gestion_taller.settings_ensayo"
EXPECTED_DB="egarage_db_ensayo"
LOG_FILE="${APP_DIR}/ensayo_fase2_$(date +%Y%m%d_%H%M).log"

exec > >(tee -a "$LOG_FILE") 2>&1

echo "============================================================"
echo "  ENSAYO — Fase 1 + Fase 2 VehiculoDesarme"
echo "  Log: $LOG_FILE"
echo "  Inicio: $(date)"
echo "============================================================"

# -----------------------------------------------------------------------------
# HELPER: verificación doble (Django + Postgres) antes de cada paso.
# Aborta si cualquiera no dice exactamente "egarage_db_ensayo".
# -----------------------------------------------------------------------------
verify_db() {
    local label="$1"
    echo ""
    echo "  [VERIFY] ${label} — verificando base activa..."

    local django_name
    django_name=$(
        DJANGO_SETTINGS_MODULE="$SETTINGS_ENSAYO" \
        python manage.py shell -c \
        "from django.conf import settings; print(settings.DATABASES['default']['NAME'])" \
        2>/dev/null | tr -d ' \n\r'
    )
    if [[ "$django_name" != "$EXPECTED_DB" ]]; then
        echo "  !! ABORT: Django NAME='${django_name}' — se esperaba '${EXPECTED_DB}'"
        exit 1
    fi
    echo "  [OK] Django NAME: ${django_name}"

    local pg_name
    pg_name=$(
        DJANGO_SETTINGS_MODULE="$SETTINGS_ENSAYO" \
        python manage.py dbshell -- -t -c "SELECT current_database();" \
        2>/dev/null | tr -d ' \n\r'
    )
    if [[ "$pg_name" != "$EXPECTED_DB" ]]; then
        echo "  !! ABORT: Postgres current_database()='${pg_name}' — se esperaba '${EXPECTED_DB}'"
        exit 1
    fi
    echo "  [OK] Postgres current_database(): ${pg_name}"
}

# =============================================================================
# SETUP — Directorio, venv, credenciales Postgres
# =============================================================================
echo ""
echo "============================================================"
echo "SETUP"
echo "============================================================"

echo ""
echo "[SETUP 1] Directorio y venv"
cd "$APP_DIR"
if [[ -f "${APP_DIR}/venv/bin/activate" ]]; then
    source "${APP_DIR}/venv/bin/activate"
    echo "  [OK] venv local: ${APP_DIR}/venv"
else
    source "/srv/egarage/venv/bin/activate"
    echo "  [OK] venv compartido: /srv/egarage/venv"
fi
echo "  [OK] Directorio: $(pwd)"
echo "  [OK] Python: $(which python)"

echo ""
echo "[SETUP 2] Extraer credenciales Postgres desde settings_prod (PGPASSWORD nunca manual)"
export PGPASSWORD
PGPASSWORD=$(
    DJANGO_SETTINGS_MODULE="$SETTINGS_PROD" \
    python manage.py shell -c \
    "from django.conf import settings; print(settings.DATABASES['default']['PASSWORD'])" \
    2>/dev/null | tr -d ' \n\r'
)
if [[ -z "$PGPASSWORD" ]]; then
    echo "  !! ABORT: PGPASSWORD vacío — revisa DJANGO_DB_PASSWORD"
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

if [[ "$PG_SOURCE_DB" == "$EXPECTED_DB" ]]; then
    echo "  !! ABORT: settings_prod apunta a '${PG_SOURCE_DB}' — coincide con el destino."
    echo "  !! settings_prod debe apuntar a la base de producción, no al ensayo."
    exit 1
fi

# =============================================================================
# FASE 0 — VERIFICACIÓN DEL CLON (ya creado manualmente)
# =============================================================================
echo ""
echo "============================================================"
echo "FASE 0 — VERIFICACIÓN DEL CLON"
echo "============================================================"

echo ""
echo "[0.1] Confirmar que egarage_db_ensayo existe"
DB_EXISTS=$(
    psql -h "$PG_HOST" -U "$PG_USER" -d postgres -t \
    -c "SELECT COUNT(*) FROM pg_database WHERE datname='${EXPECTED_DB}';" \
    | tr -d ' \n\r'
)
if [[ "$DB_EXISTS" != "1" ]]; then
    echo "  !! ABORT: egarage_db_ensayo no existe."
    echo "  !! Crear el clon primero con pg_dump/pg_restore desde egarage_db."
    exit 1
fi
echo "  [OK] egarage_db_ensayo existe"

echo ""
echo "[0.2] Confirmar descuadre 0077/0078 (estado esperado del clon fresco de producción)"
DISCUADRE=$(
    psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -t \
    -c "SELECT COUNT(*) FROM django_migrations
        WHERE app='taller'
          AND name IN ('0077_vehiculodesarme','0078_migrate_vehiculo_desarme_to_vehiculodesarme');" \
    | tr -d ' \n\r'
)
TABLA_FISICA=$(
    psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -t \
    -c "SELECT COUNT(*) FROM information_schema.tables
        WHERE table_name='taller_vehiculodesarme';" \
    | tr -d ' \n\r'
)
echo "  0077/0078 en django_migrations: ${DISCUADRE} filas (esperado: 2)"
echo "  taller_vehiculodesarme física:  ${TABLA_FISICA} (esperado: 0 = no existe aún)"
if [[ "$DISCUADRE" != "2" || "$TABLA_FISICA" != "0" ]]; then
    echo "  !! ABORT: el clon no está en el estado esperado."
    echo "  !!   Si DISCUADRE=0 y TABLA_FISICA=1, los pasos 1-6 ya se corrieron antes."
    echo "  !!   Si DISCUADRE=2 y TABLA_FISICA=1, algo intermedio fue aplicado — revisar."
    exit 1
fi
echo "  [OK] Descuadre confirmado — clon en estado correcto para iniciar"

echo ""
echo "[0.3] Confirmar que el libro está en 0136 (última migración real de producción)"
LAST_MIGRATION=$(
    psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -t \
    -c "SELECT name FROM django_migrations WHERE app='taller' ORDER BY id DESC LIMIT 1;" \
    | tr -d ' \n\r'
)
echo "  Última migración en el clon: ${LAST_MIGRATION}"
if [[ "$LAST_MIGRATION" != "0136_unique_codigo_por_empresa_vehiculo" ]]; then
    echo "  !! ABORT: se esperaba exactamente 0136. Estado inesperado del clon."
    exit 1
fi
echo "  [OK] Libro en 0136 — correcto"

echo ""
echo "[0.4] Confirmar código Fase 2 en filesystem (0142-0144 presentes, 0145 ausente)"
for f in 0142_fase2_add_vehiculo_desarme_nullable.py \
          0143_fase2_poblar_vehiculo_desarme.py \
          0144_fase2_schema_vehiculo_desarme.py; do
    if [[ ! -f "${APP_DIR}/taller/migrations/${f}" ]]; then
        echo "  !! ABORT: falta ${APP_DIR}/taller/migrations/${f}"
        exit 1
    fi
    echo "  [OK] ${f} presente"
done
if [[ -f "${APP_DIR}/taller/migrations/0145_fase2_limpieza_vehiculo.py" ]]; then
    echo "  !! ABORT: 0145 está en el filesystem — debe estar ausente en este ensayo."
    echo "  !! Eliminar 0145 antes de continuar."
    exit 1
fi
echo "  [OK] 0145 ausente (correcto)"

echo ""
echo "[0.5] Conteos de referencia en el clon (deben igualar producción)"
psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -c "
SELECT
  (SELECT COUNT(*) FROM taller_vehiculo WHERE tipo_uso='DESARME') AS vehiculos_desarme_src,
  (SELECT COUNT(*) FROM taller_empresa)                           AS empresas,
  (SELECT COUNT(*) FROM taller_piezadesarme)                     AS piezas,
  (SELECT COUNT(*) FROM taller_vehiculofinancialsnapshot)        AS snapshots,
  (SELECT COUNT(*) FROM taller_vehiclefinancialevent)            AS events;"

echo ""
read -r -p "  ¿Los conteos coinciden con producción? [s/N] " CONFIRM
if [[ "$CONFIRM" != "s" && "$CONFIRM" != "S" ]]; then
    echo "  Abortando por confirmación del usuario."
    exit 1
fi
echo "  [OK] Fase 0 completada — clon verificado, procediendo"

# =============================================================================
# PASO 1 — Desmarcar 0077-0139 del libro (--fake a 0076)
# =============================================================================
echo ""
echo "────────────────────────────────────────────────────────────"
echo "[PASO 1/10] Desmarcar 0077-0139 del libro (--fake a 0076, sin SQL en la DB)"
echo "────────────────────────────────────────────────────────────"
verify_db "Paso 1"

DJANGO_SETTINGS_MODULE="$SETTINGS_ENSAYO" \
    python manage.py migrate taller 0076 --fake
echo "  [OK] Paso 1 ejecutado"

echo ""
echo "  [CHECK EXTRA] Solo taller debe tener migraciones pendientes..."
DJANGO_SETTINGS_MODULE="$SETTINGS_ENSAYO" python manage.py shell -c "
from django.db.migrations.executor import MigrationExecutor
from django.db import connection
executor = MigrationExecutor(connection)
plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
bad_apps = sorted({m.app_label for m, _ in plan if m.app_label != 'taller'})
if bad_apps:
    print('ERROR: apps con migraciones desmarcadas además de taller:', bad_apps)
    raise SystemExit(1)
pending = [m.name for m, _ in plan if m.app_label == 'taller']
print(f'OK: solo taller pendiente ({len(pending)} migraciones)')
print('  Primeras 5:', pending[:5])
"
echo "  [OK] Check extra Paso 1 pasado"

# =============================================================================
# PASO 2 — Crear la tabla taller_vehiculodesarme (0077 real)
# =============================================================================
echo ""
echo "────────────────────────────────────────────────────────────"
echo "[PASO 2/10] Crear tabla taller_vehiculodesarme (0077 real, sin --fake)"
echo "────────────────────────────────────────────────────────────"
verify_db "Paso 2"

DJANGO_SETTINGS_MODULE="$SETTINGS_ENSAYO" \
    python manage.py migrate taller 0077
echo "  [OK] Paso 2 ejecutado"

echo ""
echo "  [CHECK] Columnas de taller_vehiculodesarme:"
psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -c "\d taller_vehiculodesarme"

echo ""
echo "  [CHECK EXTRA] Prueba ORM: VehiculoDesarme.objects.count()..."
DJANGO_SETTINGS_MODULE="$SETTINGS_ENSAYO" python manage.py shell -c "
from taller.models.vehiculo_desarme import VehiculoDesarme
count = VehiculoDesarme.objects.count()
print(f'ORM OK: VehiculoDesarme.objects.count() = {count}')
_ = VehiculoDesarme._meta.get_field('es_placeholder')
print('ORM OK: campo es_placeholder accesible en meta del modelo')
"
echo "  [OK] Check extra Paso 2 pasado"

# =============================================================================
# PASO 3 — Saltar data migration vieja 0078 (--fake)
# =============================================================================
echo ""
echo "────────────────────────────────────────────────────────────"
echo "[PASO 3/10] Saltar data migration vieja 0078 (--fake, sin copiar datos)"
echo "────────────────────────────────────────────────────────────"
verify_db "Paso 3"

DJANGO_SETTINGS_MODULE="$SETTINGS_ENSAYO" \
    python manage.py migrate taller 0078 --fake
echo "  [OK] Paso 3 ejecutado"

VDCOUNT=$(
    psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -t \
    -c "SELECT COUNT(*) FROM taller_vehiculodesarme;" \
    | tr -d ' \n\r'
)
if [[ "$VDCOUNT" != "0" ]]; then
    echo "  !! ABORT: taller_vehiculodesarme tiene ${VDCOUNT} filas — debe ser 0 tras fakear 0078"
    exit 1
fi
echo "  [OK] taller_vehiculodesarme vacía: ${VDCOUNT} filas (correcto)"

# =============================================================================
# PASO 4 — Re-registrar 0079-0136 como aplicadas (--fake)
# =============================================================================
echo ""
echo "────────────────────────────────────────────────────────────"
echo "[PASO 4/10] Re-registrar 0079-0136 como aplicadas (--fake, sin SQL en la DB)"
echo "────────────────────────────────────────────────────────────"
verify_db "Paso 4"

DJANGO_SETTINGS_MODULE="$SETTINGS_ENSAYO" \
    python manage.py migrate taller 0136 --fake
echo "  [OK] Paso 4 ejecutado"

echo ""
echo "  [CHECK] 0136 debe ser [X], 0137 debe ser [ ]:"
DJANGO_SETTINGS_MODULE="$SETTINGS_ENSAYO" \
    python manage.py showmigrations taller | grep -E "013[6-9]|0140"

# =============================================================================
# PASO 5 — Aplicar 0137-0139 de verdad (SugerenciaPiezaDesarme + tipo_carroceria)
# =============================================================================
echo ""
echo "────────────────────────────────────────────────────────────"
echo "[PASO 5/10] Aplicar 0137-0139 reales (SugerenciaPiezaDesarme + tipo_carroceria)"
echo "────────────────────────────────────────────────────────────"
verify_db "Paso 5"

DJANGO_SETTINGS_MODULE="$SETTINGS_ENSAYO" \
    python manage.py migrate taller 0139
echo "  [OK] Paso 5 ejecutado"

echo ""
echo "  [CHECK] taller_sugerenciapiezadesarme debe existir:"
psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -c \
    "\d taller_sugerenciapiezadesarme" | head -12

SPD_COUNT=$(
    psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -t \
    -c "SELECT COUNT(*) FROM taller_sugerenciapiezadesarme;" \
    | tr -d ' \n\r'
)
echo "  [OK] taller_sugerenciapiezadesarme filas: ${SPD_COUNT} (esperado: 0)"

VEH_MAXLEN=$(
    psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -t -c "
SELECT character_maximum_length FROM information_schema.columns
WHERE table_name='taller_vehiculo' AND column_name='tipo_carroceria';" \
    | tr -d ' \n\r'
)
if [[ "$VEH_MAXLEN" != "20" ]]; then
    echo "  !! ABORT: taller_vehiculo.tipo_carroceria max_length=${VEH_MAXLEN} (esperado: 20)"
    exit 1
fi
echo "  [OK] taller_vehiculo.tipo_carroceria max_length=${VEH_MAXLEN}"

echo ""
echo "  [CHECK] Estado libro 0136-0140:"
DJANGO_SETTINGS_MODULE="$SETTINGS_ENSAYO" \
    python manage.py showmigrations taller | grep -E "013[6-9]|0140"

# =============================================================================
# PASO 6 — Agregar 7 campos a taller_vehiculodesarme (0140 real)
# =============================================================================
echo ""
echo "────────────────────────────────────────────────────────────"
echo "[PASO 6/10] Agregar 7 campos a taller_vehiculodesarme (0140 real)"
echo "────────────────────────────────────────────────────────────"
verify_db "Paso 6"

DJANGO_SETTINGS_MODULE="$SETTINGS_ENSAYO" \
    python manage.py migrate taller 0140
echo "  [OK] Paso 6 ejecutado"

echo ""
echo "  [CHECK] Schema final de taller_vehiculodesarme:"
psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -c "\d taller_vehiculodesarme"

FIELD_COUNT=$(
    psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -t -c "
SELECT COUNT(*) FROM information_schema.columns
WHERE table_name = 'taller_vehiculodesarme'
  AND column_name IN (
    'es_placeholder','tipo_carroceria','precio_compra',
    'monto_chatarra','transporte_grua_desarme',
    'otros_gastos_desarme','vendedor_desarme_id'
  );" | tr -d ' \n\r'
)
if [[ "$FIELD_COUNT" != "7" ]]; then
    echo "  !! ABORT: solo ${FIELD_COUNT} de 7 campos nuevos encontrados en taller_vehiculodesarme"
    exit 1
fi
echo "  [OK] Los 7 campos nuevos presentes (${FIELD_COUNT}/7)"

# =============================================================================
# PASO 7 — 0141 real: copia Vehiculo(tipo_uso='DESARME') → VehiculoDesarme
# =============================================================================
echo ""
echo "────────────────────────────────────────────────────────────"
echo "[PASO 7/10] Data migration 0141 — copia Vehiculo DESARME → VehiculoDesarme"
echo "────────────────────────────────────────────────────────────"
verify_db "Paso 7"

# Referencia ANTES para comparar después
V_DESARME=$(
    psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -t \
    -c "SELECT COUNT(*) FROM taller_vehiculo WHERE tipo_uso='DESARME';" \
    | tr -d ' \n\r'
)
echo "  Vehiculo(tipo_uso=DESARME) en origen: ${V_DESARME} filas"

DJANGO_SETTINGS_MODULE="$SETTINGS_ENSAYO" \
    python manage.py migrate taller 0141
echo "  [OK] Paso 7 ejecutado"

# CHECK 1: VehiculoDesarme.count() == Vehiculo(DESARME).count()
VD_COUNT=$(
    psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -t \
    -c "SELECT COUNT(*) FROM taller_vehiculodesarme;" \
    | tr -d ' \n\r'
)
if [[ "$VD_COUNT" != "$V_DESARME" ]]; then
    echo "  !! ABORT: VehiculoDesarme=${VD_COUNT} != Vehiculo(DESARME)=${V_DESARME}"
    echo "  !! La migración 0141 no copió todos los registros esperados."
    exit 1
fi
echo "  [OK] VehiculoDesarme=${VD_COUNT} == Vehiculo(DESARME)=${V_DESARME}"

# CHECK 2: todos con vehiculo_origen_id NOT NULL (ningún huérfano)
ORIGIN_NULL=$(
    psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -t \
    -c "SELECT COUNT(*) FROM taller_vehiculodesarme WHERE vehiculo_origen_id IS NULL;" \
    | tr -d ' \n\r'
)
if [[ "$ORIGIN_NULL" != "0" ]]; then
    echo "  !! ABORT: ${ORIGIN_NULL} filas con vehiculo_origen_id NULL — revisar manualmente."
    exit 1
fi
echo "  [OK] Todos los VehiculoDesarme tienen vehiculo_origen_id (${ORIGIN_NULL} nulls)"

# CHECK 3: secuencia >= MAX(id) — sin riesgo de colisión futura
LAST_SEQ=$(
    psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -t \
    -c "SELECT last_value FROM taller_vehiculodesarme_id_seq;" \
    | tr -d ' \n\r'
)
MAX_ID=$(
    psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -t \
    -c "SELECT COALESCE(MAX(id), 0) FROM taller_vehiculodesarme;" \
    | tr -d ' \n\r'
)
if (( LAST_SEQ < MAX_ID )); then
    echo "  !! ABORT: secuencia (${LAST_SEQ}) < MAX(id) (${MAX_ID}) — riesgo de colisión de IDs"
    exit 1
fi
echo "  [OK] Secuencia OK: last_value=${LAST_SEQ}, MAX(id)=${MAX_ID}"

# CHECK 4: tabla de resumen
psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -c "
SELECT
  COUNT(*)                                   AS total_copiados,
  COUNT(*) FILTER (WHERE es_placeholder)     AS placeholders,
  COUNT(*) FILTER (WHERE NOT es_placeholder) AS reales,
  MIN(id)                                    AS id_min,
  MAX(id)                                    AS id_max
FROM taller_vehiculodesarme;"

# =============================================================================
# PASO 8 — 0142: AddField vehiculo_desarme nullable en 5 tablas
# =============================================================================
echo ""
echo "────────────────────────────────────────────────────────────"
echo "[PASO 8/10] AddField vehiculo_desarme nullable ×5 (0142)"
echo "────────────────────────────────────────────────────────────"
verify_db "Paso 8"

DJANGO_SETTINGS_MODULE="$SETTINGS_ENSAYO" \
    python manage.py migrate taller 0142
echo "  [OK] Paso 8 ejecutado"

# CHECK 1: las 5 columnas vehiculo_desarme_id existen
COL_COUNT=$(
    psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -t -c "
SELECT COUNT(*) FROM information_schema.columns
WHERE column_name = 'vehiculo_desarme_id'
  AND table_name IN (
    'taller_piezadesarme',
    'taller_sugerenciapiezadesarme',
    'taller_preciohistoricopieza',
    'taller_vehiculofinancialsnapshot',
    'taller_vehiclefinancialevent'
  );" | tr -d ' \n\r'
)
if [[ "$COL_COUNT" != "5" ]]; then
    echo "  !! ABORT: solo ${COL_COUNT} de 5 columnas vehiculo_desarme_id encontradas"
    exit 1
fi
echo "  [OK] Las 5 columnas vehiculo_desarme_id presentes"

# CHECK 2: todas nullable en este momento (0143 aún no corrió)
echo ""
echo "  [CHECK] Nullability de vehiculo_desarme_id (debe ser YES en todas tras 0142):"
psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -c "
SELECT table_name, is_nullable
FROM information_schema.columns
WHERE column_name = 'vehiculo_desarme_id'
  AND table_name IN (
    'taller_piezadesarme',
    'taller_sugerenciapiezadesarme',
    'taller_preciohistoricopieza',
    'taller_vehiculofinancialsnapshot',
    'taller_vehiclefinancialevent'
  )
ORDER BY table_name;"

# CHECK 3: todas aún en NULL (0143 no corrió, datos no poblados)
NULL_PIEZA=$(
    psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -t \
    -c "SELECT COUNT(*) FROM taller_piezadesarme WHERE vehiculo_desarme_id IS NOT NULL;" \
    | tr -d ' \n\r'
)
echo "  taller_piezadesarme con vehiculo_desarme_id NOT NULL: ${NULL_PIEZA} (esperado: 0)"
if [[ "$NULL_PIEZA" != "0" ]]; then
    echo "  !! ABORT: ya hay ${NULL_PIEZA} piezas con vehiculo_desarme_id — 0143 no debería haber corrido aún."
    exit 1
fi
echo "  [OK] vehiculo_desarme_id aún NULL en taller_piezadesarme (correcto, 0143 no corrió)"

# =============================================================================
# PASO 9 — 0143: top-up sync + poblar vehiculo_desarme_id en las 5 tablas
# =============================================================================
echo ""
echo "────────────────────────────────────────────────────────────"
echo "[PASO 9/10] Top-up sync + poblar vehiculo_desarme_id (0143)"
echo "────────────────────────────────────────────────────────────"
verify_db "Paso 9"

DJANGO_SETTINGS_MODULE="$SETTINGS_ENSAYO" \
    python manage.py migrate taller 0143
echo "  [OK] Paso 9 ejecutado"

# CHECK 1: 0 NULLs en las 5 tablas (0143 aborta internamente si los hay,
# pero verificamos externamente como segunda línea de defensa)
echo ""
echo "  [CHECK] NULLs en vehiculo_desarme_id por tabla (debe ser 0 en todas):"
psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -c "
SELECT
  (SELECT COUNT(*) FROM taller_piezadesarme              WHERE vehiculo_desarme_id IS NULL) AS pieza_nulls,
  (SELECT COUNT(*) FROM taller_sugerenciapiezadesarme    WHERE vehiculo_desarme_id IS NULL) AS sugerencia_nulls,
  (SELECT COUNT(*) FROM taller_preciohistoricopieza      WHERE vehiculo_desarme_id IS NULL) AS precio_nulls,
  (SELECT COUNT(*) FROM taller_vehiculofinancialsnapshot WHERE vehiculo_desarme_id IS NULL) AS snapshot_nulls,
  (SELECT COUNT(*) FROM taller_vehiclefinancialevent     WHERE vehiculo_desarme_id IS NULL) AS event_nulls;"

NULL_TOTAL=$(
    psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -t -c "
SELECT
  (SELECT COUNT(*) FROM taller_piezadesarme              WHERE vehiculo_desarme_id IS NULL) +
  (SELECT COUNT(*) FROM taller_sugerenciapiezadesarme    WHERE vehiculo_desarme_id IS NULL) +
  (SELECT COUNT(*) FROM taller_preciohistoricopieza      WHERE vehiculo_desarme_id IS NULL) +
  (SELECT COUNT(*) FROM taller_vehiculofinancialsnapshot WHERE vehiculo_desarme_id IS NULL) +
  (SELECT COUNT(*) FROM taller_vehiclefinancialevent     WHERE vehiculo_desarme_id IS NULL);" \
    | tr -d ' \n\r'
)
if [[ "$NULL_TOTAL" != "0" ]]; then
    echo "  !! ABORT: ${NULL_TOTAL} NULLs totales en vehiculo_desarme_id tras 0143."
    echo "  !! 0143 debió haber abortado internamente — verificar logs de la migración."
    exit 1
fi
echo "  [OK] 0 NULLs en las 5 tablas"

# CHECK 2: integridad referencial — vehiculo_desarme_id apunta a VehiculoDesarme real
HUERFANOS=$(
    psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -t -c "
SELECT COUNT(*) FROM taller_piezadesarme p
WHERE p.vehiculo_desarme_id NOT IN (SELECT id FROM taller_vehiculodesarme);" \
    | tr -d ' \n\r'
)
if [[ "$HUERFANOS" != "0" ]]; then
    echo "  !! ABORT: ${HUERFANOS} piezas con vehiculo_desarme_id sin VehiculoDesarme correspondiente."
    exit 1
fi
echo "  [OK] vehiculo_desarme_id en taller_piezadesarme referencia VehiculoDesarme válido (0 huérfanos)"

# =============================================================================
# PASO 10 — 0144: NOT NULL + reemplazar constraints e índices en las 5 tablas
# =============================================================================
echo ""
echo "────────────────────────────────────────────────────────────"
echo "[PASO 10/10] NOT NULL + reemplazar constraints e índices (0144)"
echo "────────────────────────────────────────────────────────────"
verify_db "Paso 10"

DJANGO_SETTINGS_MODULE="$SETTINGS_ENSAYO" \
    python manage.py migrate taller 0144
echo "  [OK] Paso 10 ejecutado"

# CHECK 1: vehiculo_desarme_id es NOT NULL en las 5 tablas
echo ""
echo "  [CHECK] Nullability tras 0144 (debe ser NO en todas):"
psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -c "
SELECT table_name, is_nullable
FROM information_schema.columns
WHERE column_name = 'vehiculo_desarme_id'
  AND table_name IN (
    'taller_piezadesarme',
    'taller_sugerenciapiezadesarme',
    'taller_preciohistoricopieza',
    'taller_vehiculofinancialsnapshot',
    'taller_vehiclefinancialevent'
  )
ORDER BY table_name;"

NOT_NULL_COUNT=$(
    psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -t -c "
SELECT COUNT(*) FROM information_schema.columns
WHERE column_name = 'vehiculo_desarme_id'
  AND is_nullable = 'NO'
  AND table_name IN (
    'taller_piezadesarme',
    'taller_sugerenciapiezadesarme',
    'taller_preciohistoricopieza',
    'taller_vehiculofinancialsnapshot',
    'taller_vehiclefinancialevent'
  );" | tr -d ' \n\r'
)
if [[ "$NOT_NULL_COUNT" != "5" ]]; then
    echo "  !! ABORT: solo ${NOT_NULL_COUNT} de 5 columnas vehiculo_desarme_id son NOT NULL"
    exit 1
fi
echo "  [OK] Las 5 columnas vehiculo_desarme_id son NOT NULL"

# CHECK 2: constraints nuevos presentes
NEW_CON_COUNT=$(
    psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -t -c "
SELECT COUNT(*) FROM pg_constraint
WHERE conname IN (
  'unique_codigo_por_empresa_vehiculo_desarme',
  'unique_sugerencia_por_vehiculo_desarme'
);" | tr -d ' \n\r'
)
if [[ "$NEW_CON_COUNT" != "2" ]]; then
    echo "  !! ABORT: solo ${NEW_CON_COUNT} de 2 constraints nuevos encontrados."
    exit 1
fi
echo "  [OK] Los 2 constraints nuevos presentes (unique_*_vehiculo_desarme)"

# CHECK 3: constraints viejos eliminados
OLD_CON_COUNT=$(
    psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -t -c "
SELECT COUNT(*) FROM pg_constraint
WHERE conname IN (
  'unique_codigo_por_empresa_vehiculo',
  'unique_sugerencia_por_vehiculo'
);" | tr -d ' \n\r'
)
if [[ "$OLD_CON_COUNT" != "0" ]]; then
    echo "  !! ABORT: ${OLD_CON_COUNT} constraints viejos aún presentes — 0144 no los eliminó."
    exit 1
fi
echo "  [OK] Los 2 constraints viejos eliminados"

# CHECK 4: índices nuevos presentes (6 nuevos de Fase 2)
echo ""
echo "  [CHECK] Índices nuevos de Fase 2:"
psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -c "
SELECT tablename, indexname
FROM pg_indexes
WHERE indexname IN (
  'taller_piez_empresa_0d4562_idx',
  'sug_pieza_emp_veh_d_idx',
  'sug_pieza_emp_veh_d_est_idx',
  'taller_vehi_vehicul_ac46db_idx',
  'taller_vehi_vehicul_13b81d_idx',
  'taller_vehi_vehicul_a36d4a_idx'
)
ORDER BY tablename, indexname;"

NEW_IDX_COUNT=$(
    psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -t -c "
SELECT COUNT(*) FROM pg_indexes
WHERE indexname IN (
  'taller_piez_empresa_0d4562_idx',
  'sug_pieza_emp_veh_d_idx',
  'sug_pieza_emp_veh_d_est_idx',
  'taller_vehi_vehicul_ac46db_idx',
  'taller_vehi_vehicul_13b81d_idx',
  'taller_vehi_vehicul_a36d4a_idx'
);" | tr -d ' \n\r'
)
if [[ "$NEW_IDX_COUNT" != "6" ]]; then
    echo "  !! ABORT: solo ${NEW_IDX_COUNT} de 6 índices nuevos encontrados."
    exit 1
fi
echo "  [OK] Los 6 índices nuevos de Fase 2 presentes"

# CHECK 5: índices viejos eliminados (6 viejos sobre columna vehiculo_id)
OLD_IDX_COUNT=$(
    psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -t -c "
SELECT COUNT(*) FROM pg_indexes
WHERE indexname IN (
  'taller_piez_empresa_864ad2_idx',
  'sug_pieza_emp_veh_idx',
  'sug_pieza_emp_veh_est_idx',
  'taller_vehi_vehicul_10a0fd_idx',
  'taller_vehi_vehicul_d07196_idx',
  'taller_vehi_vehicul_211445_idx'
);" | tr -d ' \n\r'
)
if [[ "$OLD_IDX_COUNT" != "0" ]]; then
    echo "  !! ABORT: ${OLD_IDX_COUNT} índices viejos aún presentes — 0144 no los eliminó."
    exit 1
fi
echo "  [OK] Los 6 índices viejos eliminados"

# CHECK 6: vehiculo_id AÚN EXISTE en taller_piezadesarme (0145 no debe haber corrido)
VID_EXISTS=$(
    psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -t -c "
SELECT COUNT(*) FROM information_schema.columns
WHERE table_name='taller_piezadesarme' AND column_name='vehiculo_id';" \
    | tr -d ' \n\r'
)
if [[ "$VID_EXISTS" != "1" ]]; then
    echo "  !! ABORT: vehiculo_id no existe en taller_piezadesarme — ¿se aplicó 0145 accidentalmente?"
    exit 1
fi
echo "  [OK] vehiculo_id aún presente en taller_piezadesarme (0145 no corrió — correcto)"

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
echo "[FINAL 2] Sin migraciones pendientes (0145 está en el plan pero NO en el filesystem)"
if DJANGO_SETTINGS_MODULE="$SETTINGS_ENSAYO" python manage.py migrate --check 2>&1; then
    echo "  [OK] No hay migraciones pendientes"
else
    echo "  [!] Migraciones pendientes — lista:"
    DJANGO_SETTINGS_MODULE="$SETTINGS_ENSAYO" \
        python manage.py showmigrations taller | grep "\[ \]" || true
    echo "  Si la lista está vacía, el error de --check es otro — revisar."
fi

echo ""
echo "[FINAL 3] Integridad final: conteos post-migración"
psql -h "$PG_HOST" -U "$PG_USER" -d "$EXPECTED_DB" -c "
SELECT
  (SELECT COUNT(*) FROM taller_vehiculodesarme)                                          AS total_vd,
  (SELECT COUNT(*) FROM taller_piezadesarme)                                             AS total_piezas,
  (SELECT COUNT(*) FROM taller_piezadesarme WHERE vehiculo_desarme_id IS NOT NULL)       AS piezas_con_vd,
  (SELECT COUNT(*) FROM taller_vehiculofinancialsnapshot)                                AS snapshots,
  (SELECT COUNT(*) FROM taller_vehiculofinancialsnapshot WHERE vehiculo_desarme_id IS NOT NULL) AS snapshots_con_vd,
  (SELECT COUNT(*) FROM taller_vehiclefinancialevent)                                    AS events,
  (SELECT COUNT(*) FROM taller_vehiclefinancialevent WHERE vehiculo_desarme_id IS NOT NULL) AS events_con_vd;"

echo ""
echo "[FINAL 4] Estado del libro 0136-0144:"
DJANGO_SETTINGS_MODULE="$SETTINGS_ENSAYO" \
    python manage.py showmigrations taller | grep -E "013[6-9]|014[0-4]"

echo ""
echo "============================================================"
echo "  ENSAYO COMPLETADO"
echo "  Fase 1 (Pasos 1-6): 0077 fix + 0137-0140 OK"
echo "  Fase 2 (Pasos 7-10): 0141-0144 OK"
echo "  0145 NO aplicada (deferred — mínimo 14 días tras producción estable)"
echo "  Log completo en: $LOG_FILE"
echo "  Fin: $(date)"
echo "============================================================"
echo ""
echo "LIMPIEZA (correr manualmente cuando lo decidas):"
echo "  sudo -u postgres psql -c \"DROP DATABASE ${EXPECTED_DB};\""
echo "  unset PGPASSWORD"
