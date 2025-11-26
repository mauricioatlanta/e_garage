# 📋 Guía de Migración para TeamMember

## ⚠️ Importante: Ejecutar Migraciones

Antes de usar el módulo de Gestión de Equipo, debes crear y aplicar las migraciones para el modelo `TeamMember`.

## 🚀 Pasos para Migrar

### 1. Verificar que no hay errores de importación

Si hay errores al ejecutar `makemigrations`, primero solucionalos:

```bash
# Verificar que Python puede importar el modelo
python manage.py shell
>>> from taller.models import TeamMember
>>> TeamMember
# Si no hay error, puedes continuar
```

### 2. Crear la migración

```bash
python manage.py makemigrations taller
```

Esto creará un archivo de migración en `taller/migrations/` con un nombre como:
- `00XX_create_team_member.py`

### 3. Aplicar la migración

```bash
python manage.py migrate taller
```

O para aplicar todas las migraciones pendientes:

```bash
python manage.py migrate
```

### 4. Verificar que se creó la tabla

**SQLite:**
```bash
python manage.py dbshell
.tables
# Debes ver: taller_team_member
```

**PostgreSQL:**
```bash
python manage.py dbshell
\dt taller_*
# Debes ver: taller_team_member
```

## 📊 Estructura de la Tabla

La migración creará la siguiente tabla:

```sql
CREATE TABLE taller_team_member (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    empresa_id INTEGER NOT NULL,
    rol VARCHAR(50) NOT NULL DEFAULT 'Vendedor',
    is_active BOOLEAN NOT NULL DEFAULT 1,
    fecha_creacion DATETIME NOT NULL,
    fecha_actualizacion DATETIME NOT NULL,
    creado_por_id INTEGER,
    notas TEXT,
    FOREIGN KEY (user_id) REFERENCES auth_user (id),
    FOREIGN KEY (empresa_id) REFERENCES taller_empresa (id),
    FOREIGN KEY (creado_por_id) REFERENCES auth_user (id),
    UNIQUE (user_id, empresa_id)
);
```

## 🔍 Verificar que Funciona

Después de aplicar la migración, puedes verificar:

```bash
python manage.py shell
>>> from taller.models import TeamMember
>>> TeamMember.objects.all()
<QuerySet []>
```

Si no hay errores, el módulo está listo para usar.

## 🎉 ¡Listo!

Una vez completadas las migraciones, el módulo de Gestión de Equipo estará 100% funcional.

