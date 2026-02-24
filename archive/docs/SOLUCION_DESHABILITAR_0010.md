# 🔧 Solución: Deshabilitar Migración 0010 Temporalmente

## ❌ Problema

Las migraciones 0008 y 0009 no existen o no están aplicadas, pero 0010 depende de ellas.

## ✅ Solución: Deshabilitar 0010 Temporalmente

La migración `0010_migrate_tecnico_roles` solo migra **datos** (convierte valores de roles), no cambia la estructura de la base de datos. Por lo tanto, es seguro deshabilitarla temporalmente.

### Paso 1: Renombrar el archivo

```bash
cd /home/atlantareciclajes/apps/egarage/current

# Renombrar para deshabilitar
mv taller/migrations/0010_migrate_tecnico_roles.py taller/migrations/0010_migrate_tecnico_roles.py.disabled
```

### Paso 2: Aplicar migraciones

```bash
python3.10 manage.py migrate
```

Esto debería funcionar ahora sin errores.

### Paso 3: Verificar

```bash
python3.10 diagnostico_registro.py
```

Debería funcionar sin el error de la columna `ha_usado_prueba`.

## 🔄 Re-habilitar 0010 Más Tarde (Opcional)

Si más tarde necesitas aplicar la migración 0010:

1. **Asegúrate de que 0008 y 0009 existan y estén aplicadas**
2. **Restaura el archivo:**
   ```bash
   mv taller/migrations/0010_migrate_tecnico_roles.py.disabled taller/migrations/0010_migrate_tecnico_roles.py
   ```
3. **Aplica la migración:**
   ```bash
   python3.10 manage.py migrate
   ```

## 📋 Alternativa: Verificar Última Migración Aplicada

Si quieres saber cuál es la última migración aplicada:

```bash
python3.10 manage.py shell
```

```python
from django.db import connection
cursor = connection.cursor()

# Para SQLite
cursor.execute("SELECT name FROM django_migrations WHERE app='taller' ORDER BY name DESC LIMIT 1")
row = cursor.fetchone()
if row:
    print(f"Última migración aplicada: {row[0]}")
```

Luego puedes modificar 0010 para que dependa de esa migración.

---

**Última actualización**: Diciembre 2024
