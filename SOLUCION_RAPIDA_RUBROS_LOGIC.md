# ⚡ SOLUCIÓN RÁPIDA: Error `rubros_logic` en Servidor

## ❌ Error Actual
```
ModuleNotFoundError: No module named 'taller.configuracion.rubros_logic'
```

Esto significa que el archivo `rubros_logic.py` **no existe** o **está vacío** en el servidor.

---

## 🔧 SOLUCIÓN: Crear/Reemplazar rubros_logic.py

### **OPCIÓN 1: Subir el archivo desde tu PC (Más Fácil)**

1. **En tu PC**, el archivo está en:
   ```
   E:\projecto\e_garage\taller\configuracion\rubros_logic.py
   ```

2. **En PythonAnywhere**:
   - Ir a pestaña "Files"
   - Navegar a: `/home/atlantareciclajes/apps/egarage/current/taller/configuracion/`
   - **Subir** el archivo `rubros_logic.py` desde tu PC
   - **Reemplazar** si ya existe

3. **Recargar**: Pestaña "Web" → "Reload"

---

### **OPCIÓN 2: Crear el archivo directamente en el servidor**

**En la Bash Console del servidor**, ejecuta estos comandos:

```bash
# 1. Ir al directorio del proyecto
cd /home/atlantareciclajes/apps/egarage/current

# 2. Asegurar que el directorio existe
mkdir -p taller/configuracion

# 3. Crear rubros_logic.py (copia TODO este bloque de una vez)
cat > taller/configuracion/rubros_logic.py << 'ENDOFFILE'
"""
Helpers centralizados para lógica basada en rubros.
"""

from taller.configuracion.rubros_responsables import (
    DEFAULT_RESPONSABLE_LABEL,
    RESPONSABLE_LABEL_POR_RUBRO,
)
from taller.models.tecnico import Tecnico


DEFAULT_ROLES = [Tecnico.Rol.TECNICO, Tecnico.Rol.VENDEDOR, Tecnico.Rol.MIXTO]

ROLES_POR_RUBRO = {
    "WORKSHOP": [Tecnico.Rol.TECNICO, Tecnico.Rol.MIXTO],
    "WORKSHOP_MOTO": [Tecnico.Rol.TECNICO, Tecnico.Rol.MIXTO],
    "WORKSHOP_HEAVY": [Tecnico.Rol.TECNICO, Tecnico.Rol.MIXTO],
    "EXHAUST": [Tecnico.Rol.TECNICO, Tecnico.Rol.MIXTO],
    "BODYSHOP": [Tecnico.Rol.TECNICO, Tecnico.Rol.MIXTO],
    "ELECTRIC": [Tecnico.Rol.TECNICO, Tecnico.Rol.MIXTO],
    "TIRE": [Tecnico.Rol.TECNICO, Tecnico.Rol.MIXTO],
    "PARTS": [Tecnico.Rol.VENDEDOR, Tecnico.Rol.MIXTO],
    "DETAILING": [Tecnico.Rol.TECNICO, Tecnico.Rol.VENDEDOR, Tecnico.Rol.MIXTO],
    "GLASS_AUDIO": [Tecnico.Rol.TECNICO, Tecnico.Rol.VENDEDOR, Tecnico.Rol.MIXTO],
    "FLEET": [Tecnico.Rol.TECNICO, Tecnico.Rol.MIXTO],
    "MIXED": [Tecnico.Rol.TECNICO, Tecnico.Rol.VENDEDOR, Tecnico.Rol.MIXTO],
}


def get_responsable_label(config):
    """Devuelve la etiqueta del responsable según la configuración."""
    if config:
        return config.get_responsable_label()
    return DEFAULT_RESPONSABLE_LABEL


def get_roles_permitidos(config):
    """Devuelve los roles permitidos para el campo técnico responsable."""
    rubro = getattr(config, "rubro_principal", None)
    if not rubro:
        return DEFAULT_ROLES
    return ROLES_POR_RUBRO.get(rubro, DEFAULT_ROLES)


def get_ui_config(config):
    """Devuelve la configuración de UI para el formulario de documentos."""
    if config and hasattr(config, "get_ui_config"):
        return config.get_ui_config()
    return {
        "show_vehicle": True,
        "show_technician": True,
        "show_client": True,
    }
ENDOFFILE

# 4. Verificar que se creó
ls -lh taller/configuracion/rubros_logic.py

# 5. Verificar contenido (debe mostrar las primeras líneas)
head -10 taller/configuracion/rubros_logic.py

# 6. Limpiar cache
find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null

# 7. Probar importación
python manage.py shell -c "from taller.configuracion.rubros_logic import get_responsable_label; print('✅ OK')"
```

**Si el comando del paso 7 muestra "✅ OK", el archivo está correcto.**

---

## ✅ VERIFICACIÓN FINAL

Después de crear el archivo:

1. **Verificar que existe**:
   ```bash
   ls -la taller/configuracion/
   ```
   Debe mostrar 3 archivos:
   - `__init__.py`
   - `rubros_logic.py` ← **Este es el que falta**
   - `rubros_responsables.py`

2. **Verificar tamaño** (no debe estar vacío):
   ```bash
   wc -l taller/configuracion/rubros_logic.py
   ```
   Debe mostrar alrededor de 50-60 líneas

3. **Recargar aplicación**:
   - PythonAnywhere → Pestaña "Web" → "Reload"

4. **Probar la aplicación**:
   - El error `ModuleNotFoundError: No module named 'taller.configuracion.rubros_logic'` debe desaparecer

---

## 🐛 Si sigue dando error

1. **Verificar que `rubros_responsables.py` también existe**:
   ```bash
   ls -la taller/configuracion/rubros_responsables.py
   ```

2. **Verificar permisos**:
   ```bash
   chmod 644 taller/configuracion/*.py
   ```

3. **Verificar que `__init__.py` no está vacío**:
   ```bash
   cat taller/configuracion/__init__.py
   ```

4. **Limpiar todo el cache**:
   ```bash
   find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null
   find . -type f -name "*.pyc" -delete 2>/dev/null
   ```

