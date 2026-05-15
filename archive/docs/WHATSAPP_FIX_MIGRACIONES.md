# 🔧 Solución al Problema de Migraciones de WhatsApp

## Problema

Django no reconoce la app `whatsapp` al ejecutar `makemigrations` o `migrate`, aunque esté en `INSTALLED_APPS`.

Error:
```
RuntimeError: Model class whatsapp.models.EmpresaWhatsAppConfig doesn't declare an explicit app_label and isn't in an application in INSTALLED_APPS.
```

## Solución Temporal

La migración ya está creada manualmente en `whatsapp/migrations/0001_initial.py`. 

### Opción 1: Aplicar migración directamente con SQL

Si tienes acceso a la base de datos, puedes ejecutar el SQL directamente:

```sql
-- Crear tabla whatsapp_empresa_config
CREATE TABLE whatsapp_empresa_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone_number_id VARCHAR(50) NOT NULL,
    allowed_operator_phone VARCHAR(20) NOT NULL,
    is_enabled BOOLEAN NOT NULL DEFAULT 1,
    enable_audio BOOLEAN NOT NULL DEFAULT 1,
    enable_ocr BOOLEAN NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    empresa_id INTEGER NOT NULL UNIQUE,
    FOREIGN KEY (empresa_id) REFERENCES taller_empresa(id)
);

-- Crear tabla whatsapp_sessions
CREATE TABLE whatsapp_sessions (
    operator_phone VARCHAR(20) PRIMARY KEY,
    estado VARCHAR(50) NOT NULL DEFAULT 'IDLE',
    contexto TEXT NOT NULL DEFAULT '{}',
    last_interaction DATETIME NOT NULL,
    created_at DATETIME NOT NULL,
    empresa_id INTEGER NOT NULL,
    FOREIGN KEY (empresa_id) REFERENCES taller_empresa(id)
);

-- Crear índices
CREATE INDEX whatsapp_se_empresa__idx ON whatsapp_sessions(empresa_id, estado);
CREATE INDEX whatsapp_se_last_in_idx ON whatsapp_sessions(last_interaction);
```

Luego marcar la migración como aplicada:

```bash
python manage.py migrate whatsapp 0001 --fake
```

### Opción 2: Verificar configuración de la app

Asegúrate de que:

1. ✅ `whatsapp/apps.py` existe y tiene `class WhatsAppConfig(AppConfig)`
2. ✅ `whatsapp/__init__.py` existe (puede estar vacío)
3. ✅ `whatsapp/models.py` existe con los modelos
4. ✅ `whatsapp/migrations/__init__.py` existe
5. ✅ `whatsapp/migrations/0001_initial.py` existe

### Opción 3: Recrear la app

Si nada funciona, puedes recrear la app:

```bash
# Eliminar la app (cuidado: esto eliminará los archivos)
rm -rf whatsapp

# Recrear la app
python manage.py startapp whatsapp

# Copiar los archivos de vuelta
# (models.py, views.py, etc.)
```

## Verificación

Después de aplicar la solución, verifica:

```bash
python manage.py check
python manage.py showmigrations whatsapp
python manage.py migrate
```

## Nota

El servidor Django puede funcionar correctamente aunque las migraciones no se reconozcan, siempre que las tablas existan en la base de datos. El problema es específico del sistema de migraciones de Django.
