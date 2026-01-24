# Solución para Migraciones de Marketplace

## Problema
Las migraciones de marketplace tienen dependencias de migraciones de `taller` que no existen en el servidor.

## Solución Paso a Paso

### 1. Verificar qué migraciones de taller existen en el servidor

Ejecuta en el servidor:
```bash
python manage.py showmigrations taller
```

Esto mostrará todas las migraciones de taller disponibles. Busca la **última migración aplicada** (marcada con `[X]`).

### 2. Actualizar las dependencias en las migraciones de marketplace

Una vez que sepas qué migración de taller existe, edita estos archivos:

**Archivo: `marketplace/migrations/0001_initial.py`**
```python
dependencies = [
    ("taller", "NOMBRE_DE_LA_MIGRACION_QUE_EXISTE"),  # ← Cambiar aquí
]
```

**Archivo: `marketplace/migrations/0002_whatsappenvio.py`**
```python
dependencies = [
    ("marketplace", "0001_initial"),
    ("taller", "NOMBRE_DE_LA_MIGRACION_QUE_EXISTE"),  # ← Cambiar aquí
]
```

### 3. Opciones de migraciones comunes de taller

Si no estás seguro, prueba con estas en orden:

1. `0001_initial_migration` (migración inicial alternativa)
2. `0002_initial` (segunda migración inicial)
3. `0011_improve_empresa_model_robust` (mejora del modelo Empresa)
4. Cualquier migración que veas en `showmigrations` que esté aplicada

### 4. Ejecutar las migraciones

Después de actualizar las dependencias:
```bash
python manage.py migrate marketplace
```

### 5. Si aún falla

Si ninguna migración funciona, puedes crear una migración "fake" que no haga nada pero que tenga la dependencia correcta:

```bash
python manage.py makemigrations marketplace --empty
```

Luego edita la migración generada para que tenga la dependencia correcta y ejecuta:
```bash
python manage.py migrate marketplace --fake
```

## Script Automático

He creado un script `fix_marketplace_migrations.py` que intenta detectar automáticamente la migración correcta. Puedes ejecutarlo localmente antes de subir al servidor:

```bash
python fix_marketplace_migrations.py
```

Este script buscará migraciones de taller y actualizará automáticamente las dependencias en las migraciones de marketplace.
