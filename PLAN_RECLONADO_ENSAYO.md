# PLAN_RECLONADO_ENSAYO.md

Re-clonado de `egarage_db_ensayo` desde producción antes de ensayar
las migraciones de Fase 2 (0142→0143→0144).

**Contexto:**
- Servidor: `ssh -p 2222 root@159.223.200.106`
- Producción: `/srv/egarage/` → base `egarage_db`
- Ensayo:     `/srv/egarage_ensayo/` → base `egarage_db_ensayo`
- NO correr `migrate` todavía — solo re-clonar y verificar código.

**Regla de parada:** si cualquier bloque produce output inesperado
(error de permisos, exit code ≠ 0 en restore, nombre de base incorrecto
en bloque 1-2), pegar el output completo y **no avanzar al siguiente
bloque** hasta confirmación explícita.

---

## BLOQUE 1 — Verificar estado actual (sin tocar nada)

```bash
sudo -u postgres psql -c "\l" | grep -E "Name|egarage|---"
```

Resultado esperado: verás `egarage_db` (prod) y posiblemente
`egarage_db_ensayo` (clon viejo).

---

## BLOQUE 2 — Extraer credenciales de Django y doble verificación

```bash
# 2.1 Extraer desde settings de producción (PGPASSWORD nunca escrito a mano)
eval $(cd /srv/egarage && source venv/bin/activate && \
  DJANGO_SETTINGS_MODULE=gestion_taller.settings_prod python -c "
import django, os, sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'gestion_taller.settings_prod'
django.setup()
from django.conf import settings
db = settings.DATABASES['default']
assert 'postgresql' in db.get('ENGINE',''), 'FATAL: engine=%r' % db.get('ENGINE')
sys.stdout.write(\"PGPASSWORD='%s'\nDB_NAME='%s'\nDB_USER='%s'\nDB_HOST='%s'\nDB_PORT='%s'\n\" % (
    db['PASSWORD'], db['NAME'], db['USER'],
    db.get('HOST','127.0.0.1'), db.get('PORT','5432')
))
")
export PGPASSWORD DB_NAME DB_USER DB_HOST DB_PORT

# 2.2 Confirmar (el password nunca se imprime)
echo "ENGINE=postgresql  NAME=$DB_NAME  USER=$DB_USER  HOST=$DB_HOST  PORT=$DB_PORT  PASS_SET=$([ -n \"$PGPASSWORD\" ] && echo SI || echo NO)"
```

Resultado esperado: `ENGINE=postgresql NAME=egarage_db USER=egarage HOST=127.0.0.1 PORT=5432 PASS_SET=SI`
Si ENGINE no es postgresql o PASS_SET=NO → **parar**.

```bash
# 2.3 Doble verificación: current_database() contra producción
PGPASSWORD=$PGPASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME \
  -c "SELECT current_database(), count(*) AS total_vehiculos FROM taller_vehiculo;"
```

Resultado esperado: `current_database = egarage_db`. Si dice otra cosa → **parar**.

---

## BLOQUE 3 — Drop del clon viejo + pg_dump + pg_restore

```bash
# 3.1 Dropear clon viejo (solo después de confirmar bloque 2)
sudo -u postgres psql -c "DROP DATABASE IF EXISTS egarage_db_ensayo;"
echo "DROP EXIT: $?"

# 3.2 pg_dump de producción (formato custom)
DUMP_FILE="/tmp/egarage_dump_$(date +%Y%m%d_%H%M%S).dump"
PGPASSWORD=$PGPASSWORD pg_dump \
  -h $DB_HOST -p $DB_PORT -U $DB_USER \
  -d $DB_NAME -F c -f $DUMP_FILE
echo "DUMP EXIT=$?  FILE=$DUMP_FILE  SIZE=$(du -sh $DUMP_FILE | cut -f1)"

# 3.3 Crear base del clon con mismo propietario
sudo -u postgres createdb egarage_db_ensayo -O $DB_USER
echo "CREATEDB EXIT: $?"

# 3.4 Restaurar dump al clon
PGPASSWORD=$PGPASSWORD pg_restore \
  -h $DB_HOST -p $DB_PORT -U $DB_USER \
  -d egarage_db_ensayo $DUMP_FILE
echo "RESTORE EXIT=$?"
```

Warnings de pg_restore sobre extensiones o roles son normales.
El exit code relevante es el de la última línea (`RESTORE EXIT`).

---

## BLOQUE 4 — Verificar y sincronizar código Fase 2

```bash
# 4.1 Verificar settings_ensayo.py apunta a egarage_db_ensayo
grep -E "egarage_db_ensayo|DB_NAME|NAME" /srv/egarage_ensayo/gestion_taller/settings_ensayo.py 2>/dev/null \
  | head -8 \
  || echo "FALTA /srv/egarage_ensayo/gestion_taller/settings_ensayo.py"

# 4.2 Verificar via Django
cd /srv/egarage_ensayo && source /srv/egarage/venv/bin/activate && \
  DJANGO_SETTINGS_MODULE=gestion_taller.settings_ensayo python -c "
import django, os, sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'gestion_taller.settings_ensayo'
django.setup()
from django.conf import settings
db = settings.DATABASES['default']
print('ENSAYO DB NAME:', db['NAME'])
assert db['NAME'] == 'egarage_db_ensayo', 'ERROR: apunta a %r' % db['NAME']
print('CHECK OK')
"

# 4.3 Comparar migraciones entre egarage y ensayo
echo "=== DIFERENCIAS EN MIGRACIONES ==="
diff <(ls /srv/egarage/taller/migrations/ | sort) \
     <(ls /srv/egarage_ensayo/taller/migrations/ | sort)
```

Resultado esperado del diff: 0142–0145 aparecen solo en egarage (líneas
con `<`). Eso es lo esperado — son las que vamos a ensayar. Si hay
diferencias en archivos anteriores a 0142, reportar antes de continuar.

```bash
# 4.4 rsync de código Fase 2 al ensayo
rsync -av \
  /srv/egarage/taller/migrations/ \
  /srv/egarage_ensayo/taller/migrations/

rsync -av \
  /srv/egarage/taller/models/ \
  /srv/egarage_ensayo/taller/models/

rsync -av \
  /srv/egarage/taller/services/ \
  /srv/egarage_ensayo/taller/services/

rsync -av \
  /srv/egarage/taller/desarme/ \
  /srv/egarage_ensayo/taller/desarme/

rsync -av \
  /srv/egarage/taller/documentos/desarme/ \
  /srv/egarage_ensayo/taller/documentos/desarme/

rsync -av \
  /srv/egarage/taller/management/ \
  /srv/egarage_ensayo/taller/management/

rsync -av \
  /srv/egarage/taller/admin.py \
  /srv/egarage_ensayo/taller/admin.py

rsync -av \
  /srv/egarage/taller/views/country_aware_auth.py \
  /srv/egarage_ensayo/taller/views/country_aware_auth.py

# 4.5 manage.py check en ensayo (debe dar 0 issues)
cd /srv/egarage_ensayo && source /srv/egarage/venv/bin/activate && \
  DJANGO_SETTINGS_MODULE=gestion_taller.settings_ensayo python manage.py check 2>&1
```

Resultado esperado: `System check identified no issues (0 silenced).`

---

## BLOQUE 5 — Verificación de conteos clon vs producción

```bash
# 5.1 Verificar nombres exactos de las tablas en el clon
PGPASSWORD=$PGPASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d egarage_db_ensayo \
  -c "SELECT tablename FROM pg_tables
      WHERE tablename ~ '(pieza|vehiculo|vehicle|suger|precio)'
        AND schemaname = 'public'
      ORDER BY tablename;"

# 5.2 Conteos en el CLON (sin migraciones aún — deben igualar producción)
echo "=== CONTEOS EN CLON FRESCO (pre-migración) ==="
PGPASSWORD=$PGPASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d egarage_db_ensayo \
  -c "SELECT
    (SELECT COUNT(*) FROM taller_piezadesarme)             AS pieza_desarme,
    (SELECT COUNT(*) FROM taller_sugerenciapiezadesarme)   AS sugerencia_pieza_desarme,
    (SELECT COUNT(*) FROM taller_preciohistoricopieza)     AS precio_historico_pieza,
    (SELECT COUNT(*) FROM taller_vehiculofinancialsnapshot) AS vehiculo_financial_snapshot,
    (SELECT COUNT(*) FROM taller_vehiclefinancialevent)    AS vehicle_financial_event;"

# 5.3 Los mismos conteos en PRODUCCIÓN (para cruzar)
echo "=== CONTEOS EN PRODUCCIÓN (referencia) ==="
PGPASSWORD=$PGPASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME \
  -c "SELECT
    (SELECT COUNT(*) FROM taller_piezadesarme)             AS pieza_desarme,
    (SELECT COUNT(*) FROM taller_sugerenciapiezadesarme)   AS sugerencia_pieza_desarme,
    (SELECT COUNT(*) FROM taller_preciohistoricopieza)     AS precio_historico_pieza,
    (SELECT COUNT(*) FROM taller_vehiculofinancialsnapshot) AS vehiculo_financial_snapshot,
    (SELECT COUNT(*) FROM taller_vehiclefinancialevent)    AS vehicle_financial_event;"
```

Resultado esperado: los 5 conteos del clon deben ser **idénticos** a
producción. Conocidos de sesiones anteriores (pueden haber variado):
`pieza_desarme ≈ 1013`, `vehiculo_financial_snapshot ≈ 45`,
`vehicle_financial_event ≈ 165`, `sugerencia_pieza_desarme = 0`,
`precio_historico_pieza = 0`.

Si clon ≠ producción en cualquier tabla → **parar y reportar**.

---

## DESPUÉS DE ESTE PLAN

Una vez que los 5 bloques confirmen todo OK, el siguiente paso es
ensayar las migraciones contra `egarage_db_ensayo`:

```
DJANGO_SETTINGS_MODULE=gestion_taller.settings_ensayo python manage.py migrate --run-syncdb 2>&1
```

Pero **no correr esto todavía** — esperar confirmación explícita
después de completar el bloque 5.
