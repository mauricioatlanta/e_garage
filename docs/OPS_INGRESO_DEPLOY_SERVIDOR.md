# Pasos en el servidor después de actualizar (Centro de Ingreso Pro)

Después de subir los archivos actualizados al servidor, ejecuta estos pasos **en el servidor** (en la raíz del proyecto, ej. `~/e_garage` o donde esté el código).

## 1. Activar entorno virtual (si usas uno)

```bash
source venv/bin/activate
# o en Windows: venv\Scripts\activate
```

## 2. Instalar dependencias (solo si agregaste algo nuevo)

El Centro de Ingreso **no obliga** a instalar EasyOCR; si no lo instalas, el botón OCR mostrará "OCR no disponible" y el flujo manual sigue funcionando.

Si quieres habilitar OCR (opcional, solo CPU):

```bash
pip install easyocr
```

## 3. Aplicar migraciones

```bash
python manage.py migrate taller
```

Esto aplica la migración `0074_ops_ingreso_registro_checklist` (modelos `RegistroKilometraje` y `ChecklistIngreso`).

## 4. Recolectar archivos estáticos

Para que `static/ops/ingreso/ingreso.js` se sirva en producción:

```bash
python manage.py collectstatic --noinput
```

(Si en producción usas `--noinput` por defecto, está bien; si no, quita `--noinput` para poder confirmar.)

## 5. Reiniciar el servidor de aplicación

Según cómo esté desplegado:

**Gunicorn (systemd):**
```bash
sudo systemctl restart gunicorn
# o el nombre exacto del servicio, ej.:
# sudo systemctl restart gunicorn-e_garage
```

**Gunicorn (supervisor):**
```bash
sudo supervisorctl restart gunicorn
```

**uWSGI:**
```bash
sudo systemctl restart uwsgi
# o
sudo supervisorctl restart uwsgi
```

**Otro:** reinicia el proceso que ejecuta Django (PM2, Docker, etc.).

## 6. Comprobar que todo responde

- Abrir el Centro de Operaciones y que cargue bien.
- Pulsar **Ingreso de Vehículo** y que cargue `/ops/ingreso/` (o `/cl/es/ops/ingreso/` / `/us/ops/ingreso/` según país).
- Si algo falla, revisar logs del servidor (gunicorn/uwsgi) y de Django.

## Resumen rápido (copiar/pegar)

```bash
cd /ruta/al/proyecto/e_garage
source venv/bin/activate
python manage.py migrate taller
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
```

## Nota: variables en `.env.prod` (source en bash)

Si en el servidor haces `source /srv/egarage/.env.prod`, **valores con `<` o `>` deben ir entre comillas** o bash los interpreta como redirección. Ejemplo:

- Incorrecto: `DEFAULT_FROM_EMAIL=eGarage <subscription@egarage.cl>` → error "syntax error near unexpected token"
- Correcto: `DEFAULT_FROM_EMAIL="eGarage <subscription@egarage.cl>"` o `DEFAULT_FROM_EMAIL='eGarage <subscription@egarage.cl>'`

Gunicorn (systemd) lee el archivo sin interpretar bash, pero si alguna vez haces `set -a; source .env.prod; set +a` en una shell, las comillas evitan el error.

Ajusta `venv`, ruta y nombre del servicio según tu servidor.

---

## Diagnóstico: Base de datos (SQLite vs PostgreSQL)

Si `python manage.py migrate` falla con **`fe_sendauth: no password supplied`** o ves `ENGINE: postgresql` con `NAME: srv/egarage/data/db.sqlite3` y `USER: ''`, suele ser que **DATABASE_URL** está mal (p. ej. URL postgres sin usuario/contraseña o con ruta de SQLite como nombre de BD). **Hay que corregir el `.env` en el servidor;** si no, Django seguirá usando la URL postgres que tenga ahí.

### Arreglo inmediato (sin desplegar código nuevo)

**Opción A – Desde la shell en el servidor (forzar SQLite):**

Django carga **`.env.local`** antes que `.env`. Si existe `.env.local`, los cambios en `.env` no se usan. Hay que tocar el archivo que realmente se carga.

```bash
cd /srv/egarage

# Ver qué archivo se usa (el que exista primero)
ls -la .env .env.local 2>/dev/null

# Aplicar SQLite en .env
if grep -q '^DATABASE_URL=' .env 2>/dev/null; then
  sed -i 's|^DATABASE_URL=.*|DATABASE_URL=sqlite:////srv/egarage/data/db.sqlite3|' .env
else
  echo 'DATABASE_URL=sqlite:////srv/egarage/data/db.sqlite3' >> .env
fi

# Si existe .env.local, aplicarlo también ahí (tiene prioridad sobre .env)
if [ -f .env.local ]; then
  if grep -q '^DATABASE_URL=' .env.local 2>/dev/null; then
    sed -i 's|^DATABASE_URL=.*|DATABASE_URL=sqlite:////srv/egarage/data/db.sqlite3|' .env.local
  else
    echo 'DATABASE_URL=sqlite:////srv/egarage/data/db.sqlite3' >> .env.local
  fi
  echo "--- .env.local (tiene prioridad) ---"
  grep DATABASE_URL .env.local
fi
echo "--- .env ---"
grep DATABASE_URL .env
```

Luego:

```bash
mkdir -p /srv/egarage/data
source venv/bin/activate
python manage.py shell -c "from django.conf import settings; print(settings.DATABASES)"
python manage.py migrate
sudo systemctl restart gunicorn
```

**Opción B – Editar a mano:** Abre `/srv/egarage/.env` y deja exactamente esta línea (sin otra `DATABASE_URL` ni variables Postgres activas):  
`DATABASE_URL=sqlite:////srv/egarage/data/db.sqlite3` (4 barras: `sqlite://` + `/srv/...`).

### Arreglo rápido en el servidor (SQLite) – resumen

1. **En el servidor**, edita el `.env` en la raíz del proyecto (ej. `/srv/egarage/.env`):

   - Para usar **solo SQLite**, deja o pon:
     ```bash
     DATABASE_URL=sqlite:////srv/egarage/data/db.sqlite3
     ```
     (las 4 barras: `sqlite://` + `/srv/...`)

   - Opcional: quita o comenta variables de Postgres para no mezclar:
     ```bash
     # DJANGO_DB_ENGINE=postgresql
     # DB_NAME=...
     # DB_USER=...
     # DB_PASSWORD=...
     ```

2. Crea el directorio de datos si no existe y vuelve a probar:
   ```bash
   mkdir -p /srv/egarage/data
   cd /srv/egarage && source venv/bin/activate
   python manage.py shell -c "from django.conf import settings; print(settings.DATABASES)"
   # Debe mostrar ENGINE: django.db.backends.sqlite3 y NAME con /srv/egarage/data/db.sqlite3
   python manage.py migrate
   sudo systemctl restart gunicorn
   ```

Si tras subir el código nuevo **sigue** saliendo postgres con USER/PASSWORD vacíos, el código hace **fallback a SQLite** cuando detecta Postgres sin contraseña; en ese caso la ruta por defecto es `data/db.sqlite3` relativo al proyecto o `SQLITE_PATH` si está definida. Aun así, conviene corregir el `.env` como arriba.

### Comprobaciones en el servidor

1. **Qué settings está usando el proceso**
   ```bash
   echo $DJANGO_SETTINGS_MODULE
   ```
   - Vacío → se usa el default de `manage.py` / `wsgi.py`: `gestion_taller.settings`
   - `gestion_taller.settings.prod` o `gestion_taller.settings_prod` → otro bloque de DB

2. **Qué base de datos ve Django**
   ```bash
   cd /srv/egarage
   source venv/bin/activate
   python manage.py shell -c "from django.conf import settings; print(settings.DATABASES)"
   ```
   Debe mostrar `ENGINE: django.db.backends.sqlite3` y `NAME` con la ruta al `.sqlite3`. Si ves `postgresql` y USER/PASSWORD vacíos, el `.env` tiene una `DATABASE_URL` postgres mal formada (o no se carga el `.env`).

3. **Que el .env se cargue**
   - `manage.py`/`wsgi` cargan `python-dotenv` y buscan `.env` en el directorio del proyecto. Si Gunicorn tiene `WorkingDirectory=/srv/egarage`, el `.env` de ese directorio se carga.
   - Si el servicio systemd no usa `EnvironmentFile=/srv/egarage/.env`, las variables solo estarán si `load_dotenv()` las lee desde disco (cwd = proyecto).

### Qué hace el código (para que no vuelva a pasar)

- **`gestion_taller/settings.py`**
  - Si `DATABASE_URL` empieza por `sqlite`, se usa **solo** SQLite (ruta de la URL).
  - PostgreSQL por variables (`DJANGO_DB_NAME` / `DB_NAME`) **solo** si hay `DJANGO_DB_PASSWORD` o `DB_PASSWORD`.
  - **Nuevo:** Si en cualquier caso queda ENGINE=postgresql pero sin `PASSWORD`, se hace **fallback a SQLite** (evita "fe_sendauth: no password supplied"). Ruta por defecto: `SQLITE_PATH` o `data/db.sqlite3`.

- **`gestion_taller/settings/prod.py`**
  - Si no hay `DATABASE_URL` o no hay contraseña para Postgres, se usa SQLite (`SQLITE_PATH` o `/srv/egarage/data/db.sqlite3`).

### Recomendación si usas solo SQLite en producción

En el `.env` del servidor:

- `DATABASE_URL=sqlite:////srv/egarage/data/db.sqlite3` (recomendado; barra inicial en `/srv/` importante)
- No dejar una URL `postgres://...` sin usuario/contraseña ni mezclar ruta SQLite con ENGINE postgres.

### Si el servidor usa `gestion_taller.settings_prod`

En ese archivo: **si `DATABASE_URL` empieza por `sqlite`, siempre se usa SQLite**. Para Postgres hace falta URL con contraseña o `DB_PASSWORD`/`DJANGO_DB_PASSWORD`.

#### Desplegar `settings_prod.py` actualizado

1. Desde tu máquina (ajusta usuario y servidor):
   ```bash
   scp gestion_taller/settings/prod.py usuario@servidor:/srv/egarage/gestion_taller/settings/prod.py
   ```

2. En el servidor, comprueba DB y reinicia:
   ```bash
   cd /srv/egarage
   source venv/bin/activate
   export DJANGO_SETTINGS_MODULE=gestion_taller.settings.prod
   python manage.py shell -c "from django.conf import settings; print(settings.DATABASES)"
   python manage.py migrate
   sudo systemctl restart gunicorn
   ```
