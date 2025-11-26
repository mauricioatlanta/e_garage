# ⚠️ IMPORTANTE: Estos comandos son para el SERVIDOR LINUX

## 🔴 NO ejecutes estos comandos en PowerShell de Windows

Estos comandos deben ejecutarse **EN EL SERVIDOR**, no en tu PC con Windows.

---

## 📋 OPCIÓN 1: Subir los archivos desde tu PC (Más Fácil)

### Paso 1: En tu PC (Windows)
Los archivos ya están en tu PC en:
- `taller/configuracion/__init__.py`
- `taller/configuracion/rubros_logic.py`
- `taller/configuracion/rubros_responsables.py`

### Paso 2: Subir al servidor
Usa FTP, SFTP, o el panel de control de PythonAnywhere para subir:
1. Crear el directorio `taller/configuracion/` en el servidor
2. Subir los 3 archivos a ese directorio

### Paso 3: En el servidor (Bash Console de PythonAnywhere)
```bash
# Verificar que los archivos están
ls -la taller/configuracion/

# Debe mostrar:
# __init__.py
# rubros_logic.py
# rubros_responsables.py
```

---

## 📋 OPCIÓN 2: Crear archivos directamente en el servidor

### Conectarse al servidor
1. Ir a PythonAnywhere → pestaña "Consoles"
2. Abrir una "Bash console"
3. Ir al directorio del proyecto:
   ```bash
   cd /home/atlantareciclajes/apps/egarage/current
   ```

### Crear directorio
```bash
mkdir -p taller/configuracion
```

### Crear __init__.py
```bash
cat > taller/configuracion/__init__.py << 'EOF'
"""
Módulo de configuración para rubros y reglas de negocio específicas por rubro.
"""
EOF
```

### Crear rubros_responsables.py
```bash
cat > taller/configuracion/rubros_responsables.py << 'EOF'
"""
Configuración de etiquetas de responsable según el rubro de la empresa.
"""

RESPONSABLE_LABEL_POR_RUBRO = {
    "WORKSHOP": "Mecánico responsable",
    "WORKSHOP_MOTO": "Mecánico responsable",
    "WORKSHOP_HEAVY": "Mecánico responsable",
    "EXHAUST": "Mecánico responsable",
    "BODYSHOP": "Mecánico responsable",
    "ELECTRIC": "Técnico responsable",
    "TIRE": "Técnico responsable",
    "PARTS": "Vendedor responsable",
    "DETAILING": "Técnico responsable",
    "GLASS_AUDIO": "Técnico responsable",
    "FLEET": "Técnico responsable de flota",
    "MIXED": "Responsable",
}

DEFAULT_RESPONSABLE_LABEL = "Responsable"
EOF
```

### Crear rubros_logic.py
```bash
cat > taller/configuracion/rubros_logic.py << 'EOF'
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
EOF
```

### Verificar
```bash
ls -la taller/configuracion/
```

### Verificar que Python puede importar
```bash
python manage.py shell -c "from taller.configuracion.rubros_logic import get_responsable_label; print('OK')"
```

### Recargar aplicación
- Ir a pestaña "Web" en PythonAnywhere
- Click en "Reload"

---

## ✅ RESUMEN

1. **NO ejecutes estos comandos en PowerShell de Windows**
2. **SÍ ejecútalos en el servidor Linux** (Bash console de PythonAnywhere)
3. **O sube los archivos directamente** usando FTP/SFTP desde tu PC

Los archivos que necesitas están en tu PC en:
- `E:\projecto\e_garage\taller\configuracion\__init__.py`
- `E:\projecto\e_garage\taller\configuracion\rubros_logic.py`
- `E:\projecto\e_garage\taller\configuracion\rubros_responsables.py`

