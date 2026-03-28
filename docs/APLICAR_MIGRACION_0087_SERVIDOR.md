# Aplicar migración 0087 (PiezaDesarme valorización v4 + PrecioHistoricoPieza) en servidor

**Problema:** La base de datos no tiene las columnas nuevas de `PiezaDesarme` ni la tabla `taller_preciohistoricopieza`. El código Python sí tiene los modelos actualizados, por eso falla con:

```text
django.db.utils.OperationalError: no such column: taller_piezadesarme.precio_referencia
```

**Causa:** En el servidor no existe el archivo de migración real `0087_pieza_desarme_valorizacion_v4_precio_historico.py` (solo hay un `.bak` de otra 0087). Django lee los modelos nuevos pero SQLite sigue con el esquema viejo.

**Solución:** Asegurar que la migración 0087 correcta esté en el servidor y aplicarla. No generar una 0087 nueva con `makemigrations`; usar la del repositorio.

---

## 1. Asegurar que existe la migración 0087 correcta

En el servidor, el archivo que debe existir es:

```text
taller/migrations/0087_pieza_desarme_valorizacion_v4_precio_historico.py
```

- Si **no** existe: copiarlo desde el repo (o desde este proyecto) a `taller/migrations/`.
- Si existe otro `0087_*.py` (por ejemplo `0087_plantilla_pieza_lado_zona.py`): renombrar el que no sea el de valorización a `.bak` y dejar solo `0087_pieza_desarme_valorizacion_v4_precio_historico.py`. En Django solo puede haber una migración 0087 para la app `taller`.
- **No** ejecutar `makemigrations` para “crear” 0087: si lo haces, Django puede crear `0087_piezadesarme_fecha_revision_and_more.py` y tendrías dos 0087 o conflicto de nombres. Usar siempre el archivo del repo.

Comprobar:

```bash
cd /srv/egarage
ls -la taller/migrations/0087*.py
# Debe listar solo: 0087_pieza_desarme_valorizacion_v4_precio_historico.py
```

---

## 2. Activar entorno y aplicar migración

```bash
cd /srv/egarage
source /srv/egarage/venv/bin/activate
export DJANGO_SETTINGS_MODULE=gestion_taller.settings_prod

python manage.py migrate taller
python manage.py showmigrations taller | tail -n 30
```

Debe aparecer aplicada la línea:

```text
 [X] 0087_pieza_desarme_valorizacion_v4_precio_historico
```

---

## 3. Verificar esquema en SQLite

```bash
python manage.py shell -c "
from django.db import connection
cur = connection.cursor()
print('PIEZADESARME:')
print(cur.execute('PRAGMA table_info(taller_piezadesarme)').fetchall())
print()
print('PRECIOHISTORICOPIEZA EXISTS:')
rows = cur.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name='taller_preciohistoricopieza'\").fetchall()
print(rows)
if rows:
    print(cur.execute('PRAGMA table_info(taller_preciohistoricopieza)').fetchall())
"
```

- En `taller_piezadesarme` deben aparecer columnas como: `precio_referencia`, `precio_sugerido`, `origen_precio`, `prioridad`, `revisado`, `fecha_revision`.
- Debe existir la tabla `taller_preciohistoricopieza` y su `PRAGMA table_info` debe listar sus columnas.

---

## 4. Verificar desde Django ORM

```bash
python manage.py shell -c "
from taller.models import PiezaDesarme
from django.apps import apps
PH = apps.get_model('taller','PrecioHistoricoPieza')
print('PiezaDesarme fields:', [f.name for f in PiezaDesarme._meta.fields])
print('PrecioHistoricoPieza table:', PH._meta.db_table)
print('Vehiculo tipo_uso=DESARME =', apps.get_model('taller','Vehiculo').objects.filter(tipo_uso='DESARME').count())
print('PiezaDesarme total =', PiezaDesarme.objects.count())
print('PiezaDesarme con precio_referencia field OK =', PiezaDesarme.objects.filter(precio_referencia__isnull=False).count())
print('Historico total =', PH.objects.count())
"
```

- No debe lanzar `OperationalError`.
- `PiezaDesarme fields` debe incluir `precio_referencia`, `precio_sugerido`, `origen_precio`, `prioridad`, `revisado`, `fecha_revision`.
- `PrecioHistoricoPieza table` debe ser `taller_preciohistoricopieza`.

---

## 5. Si en el servidor showmigrations termina en 0086

Entonces la migración 0087 no está aplicada. Pasos:

1. Confirmar que el único `0087_*.py` en `taller/migrations/` es `0087_pieza_desarme_valorizacion_v4_precio_historico.py`.
2. Ejecutar `python manage.py migrate taller`.
3. Repetir las comprobaciones de los puntos 3 y 4.

Solo después de que esto esté correcto tiene sentido revisar el siguiente cuello de botella: que la UI de documentos permita crear líneas con `pieza_desarme`.

---

## Resumen

| Qué | Acción |
|-----|--------|
| Archivo 0087 en servidor | Debe existir `taller/migrations/0087_pieza_desarme_valorizacion_v4_precio_historico.py` (copiar del repo si falta). |
| No crear 0087 con makemigrations | Usar solo la 0087 del repositorio; no ejecutar `makemigrations` para generar otra 0087. |
| Aplicar | `python manage.py migrate taller` |
| Verificar | `showmigrations`, PRAGMA table_info, y el script ORM de arriba. |
