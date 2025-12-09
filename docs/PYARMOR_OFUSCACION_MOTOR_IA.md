# 🔒 Guía de Ofuscación del Motor de IA con PyArmor

## Objetivo

Proteger el código fuente del motor de IA (`motor_ia_core.py`) mediante ofuscación/compilación antes del despliegue a producción, haciendo que el código sea ilegible para ingeniería inversa.

---

## 🚀 Inicio Rápido

### Opción 1: Script Automatizado (Recomendado)

```bash
# 1. Ofuscar el código
python scripts/ofuscar_motor_ia.py

# 2. Validar que funciona
python scripts/test_codigo_ofuscado.py

# 3. Desplegar (Linux/Mac)
./scripts/deploy_produccion_seguro.sh

# 3. Desplegar (Windows)
.\scripts\deploy_produccion_seguro.ps1
```

### Opción 2: Manual

Sigue las instrucciones detalladas abajo.

---

## 📋 Prerequisitos

1. **PyArmor instalado:**
   ```bash
   pip install pyarmor
   ```
   O instalar desde requirements.txt:
   ```bash
   pip install -r requirements.txt
   ```

2. **Estructura de archivos:**
   - `taller/utils/motor_ia_core.py` - Código fuente a proteger
   - `taller/utils/motor_ia.py` - Wrapper que importa el core

---

## 🚀 Proceso de Ofuscación

### Paso 1: Instalar PyArmor

```bash
pip install pyarmor
```

### Paso 2: Ofuscar el archivo core

```bash
# Desde la raíz del proyecto
pyarmor gen --recursive --output taller/utils/motor_ia_core_compiled taller/utils/motor_ia_core.py
```

**Explicación de parámetros:**
- `--recursive`: Ofusca también las dependencias
- `--output`: Directorio de salida para el código ofuscado
- Último parámetro: Archivo o directorio a ofuscar

### Paso 3: Verificar la estructura generada

PyArmor creará:
```
taller/utils/
├── motor_ia_core.py          # Código fuente (NO subir a producción)
├── motor_ia_core_compiled/   # Código ofuscado (subir a producción)
│   ├── motor_ia_core.py      # Archivo ofuscado
│   └── pytransform/          # Librerías de PyArmor
└── motor_ia.py               # Wrapper (sin cambios)
```

### Paso 4: Actualizar el wrapper para usar el código ofuscado

El archivo `motor_ia.py` ya está configurado para intentar importar el core compilado primero:

```python
try:
    # Intentar importar el core compilado primero (para producción)
    from .motor_ia_core_compiled import MotorIACore
except ImportError:
    # Fallback al código fuente (solo para desarrollo)
    from .motor_ia_core import MotorIACore
```

### Paso 5: Configurar .gitignore

Asegúrate de que `.gitignore` incluya:

```gitignore
# Código fuente del core (NO subir a producción)
taller/utils/motor_ia_core.py

# Archivos de PyArmor
taller/utils/motor_ia_core_compiled/
taller/utils/pytransform/
*.pyarmor
```

**IMPORTANTE:** El código fuente `motor_ia_core.py` NO debe estar en el repositorio de producción.

---

## 🔧 Configuración para Producción

### Opción 1: Compilación a Bytecode (.pyc)

PyArmor puede compilar a bytecode para mayor protección:

```bash
pyarmor gen --pack onefile --output taller/utils/motor_ia_core_compiled taller/utils/motor_ia_core.py
```

### Opción 2: Ofuscación con Restricciones

Para mayor seguridad, puedes agregar restricciones:

```bash
# Restringir a una IP específica (opcional, para servidores dedicados)
pyarmor gen --restrict --output taller/utils/motor_ia_core_compiled taller/utils/motor_ia_core.py
```

---

## ✅ Verificación Post-Ofuscación

### Test 1: Verificar que el código ofuscado funciona

```python
# test_ofuscacion.py
from taller.utils.motor_ia import MotorDiagnosticoIA
from taller.models import Documento

# Debe funcionar igual que antes
motor = MotorDiagnosticoIA()
documentos = Documento.objects.all()[:10]
resultados = motor.analizar_servicios_completo(documentos)

assert "servicios_crecimiento" in resultados
assert "predicciones_ingresos" in resultados
print("✅ Ofuscación verificada correctamente")
```

### Test 2: Ejecutar tests críticos

```bash
# Ejecutar el test de flujo crítico financiero
pytest tests/test_flujo_critico_financiero.py -v

# Debe pasar todos los tests
```

### Test 3: Verificar que el código fuente no está accesible

En producción, intentar leer `motor_ia_core.py` debe fallar o no existir.

---

## 📦 Proceso de Despliegue

### Desarrollo (Local)

1. Mantener `motor_ia_core.py` en el repositorio
2. Usar código fuente directamente
3. Desarrollo y debugging normales

### Producción (Servidor)

1. **NO subir `motor_ia_core.py`** al servidor
2. Subir solo `motor_ia_core_compiled/` (código ofuscado)
3. Asegurar que `motor_ia.py` pueda importar el core compilado

### Script de Despliegue

```bash
#!/bin/bash
# deploy_with_obfuscation.sh

# 1. Ofuscar el código
pyarmor gen --recursive --output taller/utils/motor_ia_core_compiled taller/utils/motor_ia_core.py

# 2. Eliminar código fuente del directorio de despliegue
rm -f deploy/taller/utils/motor_ia_core.py

# 3. Copiar código ofuscado
cp -r taller/utils/motor_ia_core_compiled deploy/taller/utils/

# 4. Continuar con despliegue normal...
```

---

## ⚠️ Consideraciones Importantes

### 1. Compatibilidad de Versiones

- PyArmor debe ser compatible con la versión de Python en producción
- Verificar compatibilidad antes de ofuscar

### 2. Dependencias

- Asegurar que todas las dependencias estén disponibles en producción
- PyArmor requiere `pytransform` en el servidor

### 3. Performance

- El código ofuscado puede tener un ligero overhead de performance
- Realizar benchmarks antes/después de ofuscación

### 4. Debugging

- El código ofuscado es difícil de debuggear
- Mantener logs detallados para troubleshooting

---

## 🔍 Troubleshooting

### Error: "No module named 'pytransform'"

**Solución:** Asegurar que `pytransform` esté en el PYTHONPATH o copiar la carpeta `pytransform/` al directorio del proyecto.

### Error: "ImportError: cannot import name 'MotorIACore'"

**Solución:** Verificar que el archivo ofuscado mantenga el nombre de la clase. PyArmor preserva los nombres de clases y funciones.

### El código ofuscado no funciona

**Solución:**
1. Verificar que todas las dependencias estén disponibles
2. Re-ofuscar con `--recursive` para incluir dependencias
3. Verificar que el wrapper `motor_ia.py` esté importando correctamente

---

## 📚 Referencias

- [Documentación PyArmor](https://pyarmor.readthedocs.io/)
- [PyArmor GitHub](https://github.com/dashingsoft/pyarmor)

---

## ✅ Checklist de Implementación

- [ ] PyArmor instalado
- [ ] Código ofuscado generado
- [ ] Tests ejecutados y pasando
- [ ] `.gitignore` configurado correctamente
- [ ] Código fuente NO en producción
- [ ] Documentación actualizada
- [ ] Script de despliegue configurado

---

**Última actualización:** 2025-12-08  
**Mantenido por:** Equipo de Desarrollo eGarage

