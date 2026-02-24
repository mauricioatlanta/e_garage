# Instrucciones para Corregir Migraciones en el Servidor

## Paso 1: Listar migraciones de taller directamente (sin usar showmigrations)

Ejecuta en el servidor:
```bash
ls -la taller/migrations/ | grep "^-" | awk '{print $9}' | grep -E "^[0-9]" | sort
```

O simplemente:
```bash
ls taller/migrations/*.py | grep -v __init__ | sort
```

Esto mostrará todos los archivos de migración de taller sin intentar cargarlos.

## Paso 2: Temporalmente deshabilitar marketplace

Edita `gestion_taller/settings.py` y comenta temporalmente la línea de marketplace:

```python
INSTALLED_APPS = [
    # ...
    "taller.apps.TallerConfig",
    "ubicacion.apps.UbicacionConfig",
    # "marketplace.apps.MarketplaceConfig",  # ← Comentar temporalmente
    # ...
]
```

Luego intenta:
```bash
python manage.py showmigrations taller
```

## Paso 3: Una vez que sepas qué migración existe

Actualiza las dependencias en:
- `marketplace/migrations/0001_initial.py`
- `marketplace/migrations/0002_whatsappenvio.py`

Y vuelve a habilitar marketplace en settings.py.

## Alternativa: Eliminar dependencia de taller

Si ninguna migración funciona, podemos hacer que las migraciones de marketplace NO dependan de taller, pero esto requiere modificar las migraciones para que no usen ForeignKey a Empresa en la creación inicial, o usar RunPython para verificar.
