# Fix: Columna `context` en taller_documento (drift de esquema)

## Causa raíz

El POST a `/us/documentos/form/` falla con:
```text
django.db.utils.IntegrityError: NOT NULL constraint failed: taller_documento.context
```

La tabla en producción tiene una columna `context` (NOT NULL, sin default) que no existe en el modelo Django ni en las migraciones. Los INSERT no incluyen ese campo y SQLite rechaza la fila.

## Solución: eliminar la columna `context`

### 1. Respaldo

```bash
cd /srv/egarage
cp db.sqlite3 db.sqlite3.backup_$(date +%F_%H%M%S)
```

### 2. Ejecución en modo dry-run (recomendado primero)

```bash
python manage.py remove_context_from_documento --dry-run
```

### 3. Ejecución real

```bash
python manage.py remove_context_from_documento
```

### 4. Comprobar

```bash
python manage.py shell -c "
from django.db import connection
c = connection.cursor()
c.execute(\"PRAGMA table_info(taller_documento)\")
cols = [r[1] for r in c.fetchall()]
print('context' in cols and '❌ context sigue' or '✅ context eliminada')
"
```

### 5. Reiniciar aplicación

```bash
sudo systemctl restart gunicorn
```

### 6. Probar creación de documento

Probar crear un documento desde la UI o:

```bash
curl -k -I --resolve www.egarage.cl:443:127.0.0.1 https://www.egarage.cl/us/documentos/form/
```

## Comando

`remove_context_from_documento`: reconstruye la tabla `taller_documento` sin la columna `context`, copiando los datos a la nueva tabla.
