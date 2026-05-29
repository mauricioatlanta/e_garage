# 🗄️ Configuración de Base de Datos - eGarage

## 📋 Resumen de Archivos de Configuración

Este proyecto tiene múltiples archivos de configuración para diferentes entornos. **Para DigitalOcean, usa `gestion_taller/settings_prod.py`**.

### Archivos de Configuración

| Archivo | Entorno | Uso |
|---------|---------|-----|
| `gestion_taller/settings.py` | Base/Desarrollo | Configuración base que heredan otros |
| `gestion_taller/settings_prod.py` | **DigitalOcean** | **✅ USA ESTE para DigitalOcean** |
| `gestion_taller/settings/production.py` | Render | Solo para despliegues en Render |
| `gestion_taller/settings/dev.py` | Desarrollo local | Para desarrollo local |

## 🔧 Configuración Actual en DigitalOcean

### Estado Actual: SQLite (Temporal)

Actualmente, `settings_prod.py` está configurado para usar **SQLite** durante la migración inicial a DigitalOcean. Esto permite que el sitio funcione inmediatamente sin necesidad de configurar PostgreSQL.

**Ubicación de la base de datos:** `/srv/egarage/db.sqlite3`

### ⚠️ Limitaciones de SQLite en Producción

- **No recomendado para múltiples workers de Gunicorn**: SQLite no maneja bien la concurrencia de escritura
- **Sin transacciones concurrentes**: Solo un proceso puede escribir a la vez
- **Sin escalabilidad**: No es adecuado para producción con tráfico alto

**Recomendación:** Migra a PostgreSQL tan pronto como sea posible.

## 🚀 Migración a PostgreSQL

### Paso 1: Instalar PostgreSQL

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

### Paso 2: Crear Base de Datos y Usuario

```bash
sudo -u postgres psql

# En la consola de PostgreSQL:
CREATE DATABASE egarage_db;
CREATE USER egarage WITH PASSWORD 'tu_password_seguro';
ALTER ROLE egarage SET client_encoding TO 'utf8';
ALTER ROLE egarage SET default_transaction_isolation TO 'read committed';
ALTER ROLE egarage SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE egarage_db TO egarage;
\q
```

### Paso 3: Configurar Variables de Entorno

Edita `/srv/egarage/.env` y agrega:

```bash
# Base de datos PostgreSQL
DJANGO_DB_ENGINE=postgresql
DJANGO_DB_NAME=egarage_db
DJANGO_DB_USER=egarage
DJANGO_DB_PASSWORD=tu_password_seguro
DJANGO_DB_HOST=127.0.0.1
DJANGO_DB_PORT=5432
```

### Paso 4: Migrar Datos de SQLite a PostgreSQL

```bash
cd /srv/egarage

# 1. Exportar datos de SQLite
python3 manage.py dumpdata --natural-foreign --natural-primary > backup_sqlite.json

# 2. Cambiar configuración a PostgreSQL (ya está en .env)
# 3. Crear tablas en PostgreSQL
python3 manage.py migrate

# 4. Cargar datos
python3 manage.py loaddata backup_sqlite.json

# 5. Verificar
python3 manage.py dbshell
# Deberías ver la consola de PostgreSQL
```

### Paso 5: Reiniciar Servicios

```bash
sudo systemctl restart gunicorn
sudo systemctl reload nginx
```

### Paso 6: Activar Validación de PostgreSQL

Una vez que PostgreSQL esté funcionando correctamente, edita `settings_prod.py` y descomenta la validación:

```python
# En settings_prod.py, busca la sección de SQLite y descomenta:
if DATABASES["default"]["ENGINE"].endswith("sqlite3"):
    raise RuntimeError(
        "SQLite NO está permitido en producción. "
        "Configura DJANGO_DB_ENGINE=postgresql en tu archivo .env"
    )
```

## 🔍 Verificación de Configuración

### Verificar qué base de datos está usando Django

```bash
cd /srv/egarage
python3 manage.py dbshell
```

- Si ves `sqlite>`, estás usando SQLite
- Si ves `egarage_db=>`, estás usando PostgreSQL

### Verificar configuración desde Python

```bash
cd /srv/egarage
python3 manage.py shell

>>> from django.conf import settings
>>> print(settings.DATABASES['default']['ENGINE'])
```

## 📝 Variables de Entorno Disponibles

### Base de Datos

| Variable | Descripción | Valor por Defecto |
|----------|-------------|-------------------|
| `DJANGO_DB_ENGINE` | Motor de BD (`sqlite3` o `postgresql`) | `sqlite3` |
| `DJANGO_DB_NAME` | Nombre de la BD o ruta de SQLite | `/srv/egarage/db.sqlite3` |
| `DJANGO_DB_USER` | Usuario de PostgreSQL | `egarage` |
| `DJANGO_DB_PASSWORD` | Contraseña de PostgreSQL | (requerido si usas PostgreSQL) |
| `DJANGO_DB_HOST` | Host de PostgreSQL | `127.0.0.1` |
| `DJANGO_DB_PORT` | Puerto de PostgreSQL | `5432` |

### SSL/HTTPS

| Variable | Descripción | Valor por Defecto |
|----------|-------------|-------------------|
| `DJANGO_SECURE_SSL_REDIRECT` | Redirigir HTTP a HTTPS | `True` |
| `DJANGO_SESSION_COOKIE_SECURE` | Cookies de sesión solo por HTTPS | `True` |
| `DJANGO_CSRF_COOKIE_SECURE` | Cookies CSRF solo por HTTPS | `True` |

**Nota:** Si no tienes certificado SSL instalado, configura `DJANGO_SECURE_SSL_REDIRECT=false` temporalmente.

## 🛠️ Solución de Problemas

### Error: "SQLite NO está permitido en producción"

**Causa:** La validación de SQLite está activada pero estás usando SQLite.

**Solución:**
1. Si estás migrando, comenta temporalmente la validación en `settings_prod.py`
2. Si ya migraste, configura `DJANGO_DB_ENGINE=postgresql` en `.env`

### Error: "DJANGO_DB_PASSWORD debe estar configurado"

**Causa:** Estás intentando usar PostgreSQL pero no configuraste la contraseña.

**Solución:**
```bash
# Agrega a /srv/egarage/.env:
DJANGO_DB_PASSWORD=tu_password_seguro
```

### Error de conexión a PostgreSQL

**Verificar que PostgreSQL esté corriendo:**
```bash
sudo systemctl status postgresql
```

**Verificar que el usuario y base de datos existan:**
```bash
sudo -u postgres psql -c "\du"  # Listar usuarios
sudo -u postgres psql -c "\l"    # Listar bases de datos
```

**Verificar permisos:**
```bash
sudo -u postgres psql -d egarage_db -c "GRANT ALL PRIVILEGES ON DATABASE egarage_db TO egarage;"
```

## 📚 Referencias

- [Django Database Settings](https://docs.djangoproject.com/en/stable/ref/settings/#databases)
- [PostgreSQL Installation Guide](https://www.postgresql.org/download/)
- [Django Migrations](https://docs.djangoproject.com/en/stable/topics/migrations/)

---

**Última actualización:** 2025-01-XX
