# 🚀 Actualizar Versión eGarage 2.1.2 al Servidor

**Fecha:** 2025-12-08  
**Versión:** 2.1.2  
**Versión Anterior:** 2.1.1  
**Servidor:** PythonAnywhere (atlantareciclajes)

---

## 📋 RESUMEN DE CAMBIOS EN v2.1.2

### Nuevas Funcionalidades
- ✅ **Sistema de Cortesías con Auditoría Interna**
- ✅ **Fix Crítico: Bug de Contraseña en iOS**
- ✅ **Implementación PWA (Progressive Web App)**
- ✅ **Mejoras en Seguridad y Gobernanza**

---

## 🔄 OPCIÓN 1: ACTUALIZACIÓN AUTOMÁTICA VIA GIT (Recomendada)

### Paso 1: Commit y Push desde tu PC

```powershell
# Agregar todos los cambios
git add -A

# Hacer commit con la nueva versión
git commit -m "chore: actualizar versión a 2.1.2 - Sistema de cortesías, fix iOS y PWA"

# Push a GitHub
git push origin main
```

### Paso 2: En el Servidor (PythonAnywhere Console)

1. **Conectarte a la consola:**
   - Ve a: https://www.pythonanywhere.com/user/atlantareciclajes/
   - Pestaña: **"Consoles"**
   - Abre una **Bash console**

2. **Ejecutar comandos de actualización:**

```bash
# Ir al directorio del proyecto
cd /home/atlantareciclajes/apps/egarage/current

# Activar entorno virtual
workon venv_egarage310

# Obtener últimos cambios
git pull origin main

# Limpiar caché de Python
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null
find . -name "*.pyc" -delete

# Aplicar migraciones (si hay nuevas)
python manage.py migrate

# Recopilar archivos estáticos (CRÍTICO para PWA y fix iOS)
python manage.py collectstatic --noinput

# Verificar versión
python manage.py shell -c "from taller.version import get_version; print('Versión:', get_version())"
# Debe mostrar: Versión: 2.1.2
```

3. **Recargar la aplicación:**
   - Ve al dashboard: https://www.pythonanywhere.com/user/atlantareciclajes/
   - Pestaña: **"Web"**
   - Clic en: **"Reload atlantareciclajes.pythonanywhere.com"**

---

## 🔄 OPCIÓN 2: ACTUALIZACIÓN MANUAL DEL ARCHIVO

Si prefieres actualizar solo el archivo de versión:

### En el Servidor (PythonAnywhere Console)

```bash
# Ir al directorio del proyecto
cd /home/atlantareciclajes/apps/egarage/current

# Activar entorno virtual
workon venv_egarage310

# Editar el archivo de versión
nano taller/version.py
```

**Cambiar estas líneas:**
```python
# ANTES:
__version__ = "2.1.1"
__version_info__ = (2, 1, 1)
__release_date__ = "2025-11-25"

# DESPUÉS:
__version__ = "2.1.2"
__version_info__ = (2, 1, 2)
__release_date__ = "2025-12-08"
```

**Guardar:** `Ctrl+O`, `Enter`, `Ctrl+X`

**Verificar:**
```bash
python manage.py shell -c "from taller.version import get_version; print('Versión:', get_version())"
# Debe mostrar: Versión: 2.1.2
```

**⚠️ IMPORTANTE:** Si actualizas manualmente, asegúrate de también:
1. Actualizar el código de las nuevas funcionalidades (cortesías, fix iOS, PWA)
2. Ejecutar `collectstatic` para los archivos estáticos nuevos
3. Reiniciar la aplicación

---

## 🔄 OPCIÓN 3: ACTUALIZACIÓN CON SED (Automática)

```bash
# Ir al directorio del proyecto
cd /home/atlantareciclajes/apps/egarage/current

# Activar entorno virtual
workon venv_egarage310

# Actualizar versión automáticamente
sed -i 's/__version__ = "2.1.1"/__version__ = "2.1.2"/' taller/version.py
sed -i 's/__version_info__ = (2, 1, 1)/__version_info__ = (2, 1, 2)/' taller/version.py
sed -i 's/__release_date__ = "2025-11-25"/__release_date__ = "2025-12-08"/' taller/version.py

# Verificar
python manage.py shell -c "from taller.version import get_version; print('Versión:', get_version())"
# Debe mostrar: Versión: 2.1.2
```

**⚠️ IMPORTANTE:** Esta opción solo actualiza el número de versión. Asegúrate de tener el código actualizado.

---

## ✅ VERIFICACIÓN POST-ACTUALIZACIÓN

### 1. Verificar Versión

```bash
python manage.py shell << 'EOF'
from taller.version import get_version, get_version_info
print("Versión:", get_version())
info = get_version_info()
print("Fecha:", info['release_date'])
print("\nChangelog:")
print(info['changelog'])
exit()
EOF
```

**Resultado esperado:**
```
Versión: 2.1.2
Fecha: 2025-12-08
```

### 2. Verificar Archivos Estáticos (CRÍTICO)

```bash
# Verificar que los archivos nuevos están presentes
ls -la staticfiles/js/ios-password-fix.js
ls -la staticfiles/manifest.json
ls -la staticfiles/sw.js
```

**Deben existir los 3 archivos**

### 3. Verificar Funcionalidades

#### A. Sistema de Cortesías
- Acceder a: `https://tu-dominio.com/admin-monitoring/cortesia/`
- Verificar que la interfaz carga correctamente

#### B. Fix iOS
- Verificar que `ios-password-fix.js` se carga en las páginas de login/registro
- Probar en iPhone real

#### C. PWA
- Verificar que `manifest.json` y `sw.js` están accesibles
- Probar instalación en dispositivo móvil

---

## 📋 CHECKLIST DE ACTUALIZACIÓN

### Pre-Actualización
- [ ] Código actualizado en repositorio (git push)
- [ ] Backup de base de datos (recomendado)
- [ ] Notificar usuarios si es necesario

### Actualización
- [ ] Conectado a consola del servidor
- [ ] Entorno virtual activado
- [ ] Código actualizado (git pull o manual)
- [ ] Migraciones aplicadas
- [ ] `collectstatic` ejecutado
- [ ] Versión verificada (2.1.2)

### Post-Actualización
- [ ] Aplicación recargada
- [ ] Archivos estáticos verificados
- [ ] Sistema de cortesías probado
- [ ] Fix iOS probado en iPhone
- [ ] PWA probada en dispositivo móvil
- [ ] Logs revisados (sin errores críticos)

---

## 🚨 SI ALGO FALLA

### Versión No Se Actualiza

**Diagnóstico:**
```bash
# Verificar que el archivo se actualizó
cat taller/version.py | grep "__version__"

# Verificar que Python puede importarlo
python manage.py shell -c "from taller.version import get_version; print(get_version())"
```

### Archivos Estáticos No Se Actualizan

**Solución:**
```bash
# Forzar recolección
python manage.py collectstatic --noinput --clear

# Verificar permisos
ls -la staticfiles/
```

### Aplicación No Recarga

**Solución:**
- Ir al dashboard de PythonAnywhere
- Pestaña "Web"
- Clic en "Reload"
- Esperar 30-60 segundos
- Verificar logs si hay errores

---

## 📞 Resumen Ejecutivo

### Cambios en v2.1.2
- ✅ Sistema de Cortesías con Auditoría
- ✅ Fix crítico de contraseña iOS
- ✅ Implementación PWA completa
- ✅ Mejoras en seguridad y gobernanza

### Pasos Críticos
1. Actualizar código en servidor
2. Ejecutar `collectstatic` (CRÍTICO)
3. Reiniciar aplicación
4. Verificar funcionalidades nuevas

---

**¡Éxito con la actualización! 🚀**





