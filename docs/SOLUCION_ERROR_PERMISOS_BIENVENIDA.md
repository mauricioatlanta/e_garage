# ===============================================================
# 🚨 SOLUCIÓN: PermissionError en Templates Django
# ===============================================================
# Error: [Errno 13] Permission denied al acceder a templates
# Afecta a: templates globales y templates de apps (taller/templates/)
# ===============================================================

## 🔍 **PROBLEMA IDENTIFICADO:**

```
PermissionError at /us/es/bienvenida/
[Errno 13] Permission denied: '/home/atlantareciclajes/apps/egarage/releases/2025-11-24_0525_eg/templates/us/es/onboarding/bienvenida.html'

PermissionError at /us/vehiculos/crear/
[Errno 13] Permission denied: '/home/atlantareciclajes/apps/egarage/current/taller/templates/taller/us/en/vehiculos/crear_vehiculo.html'
```

**CAUSA:** El proceso uwsgi (servidor web) no tiene permisos de lectura para los archivos de template. Esto afecta tanto a:
- Templates globales: `templates/`
- Templates de apps: `taller/templates/`

## 🚀 **SOLUCIÓN INMEDIATA (En el servidor):**

### Opción 1: Corregir permisos del archivo específico

```bash
# Conectarse al servidor
ssh atlantareciclajes@ssh.pythonanywhere.com

# Ir al directorio del release actual
cd /home/atlantareciclajes/apps/egarage/releases/2025-11-24_0525_eg

# Dar permisos de lectura al archivo
chmod 644 templates/us/es/onboarding/bienvenida.html

# Verificar que el archivo es legible
ls -l templates/us/es/onboarding/bienvenida.html
```

### Opción 2: Corregir permisos de todos los templates (RECOMENDADO)

```bash
# Conectarse al servidor
ssh atlantareciclajes@ssh.pythonanywhere.com

# Ir al directorio del release actual
cd /home/atlantareciclajes/apps/egarage/releases/2025-11-24_0525_eg

# Dar permisos de lectura a templates globales
find templates -type f -exec chmod 644 {} \;
find templates -type d -exec chmod 755 {} \;

# Dar permisos de lectura a templates de apps (taller/templates/, etc.)
find taller/templates -type f -exec chmod 644 {} \; 2>/dev/null || true
find taller/templates -type d -exec chmod 755 {} \; 2>/dev/null || true

# Verificar permisos
ls -la templates/us/es/onboarding/
ls -la taller/templates/taller/us/en/vehiculos/ 2>/dev/null || echo "Template de app no encontrado"
```

### Opción 3: Corregir permisos de todo el proyecto (MÁS COMPLETO)

```bash
# Conectarse al servidor
ssh atlantareciclajes@ssh.pythonanywhere.com

# Ir al directorio del release actual
cd /home/atlantareciclajes/apps/egarage/releases/2025-11-24_0525_eg

# Dar permisos correctos a archivos y directorios
find . -type f -exec chmod 644 {} \;
find . -type d -exec chmod 755 {} \;

# Dar permisos de ejecución a scripts Python
find . -name "*.py" -exec chmod 755 {} \;
chmod 755 manage.py

# Verificar que templates son legibles
ls -la templates/us/es/onboarding/bienvenida.html
```

## 🔧 **SOLUCIÓN PERMANENTE (Actualizar script de deployment):**

El script de deployment debe configurar permisos automáticamente. Ver archivo:
- `scripts/deploy_to_server.sh` (actualizado para incluir chmod)

## ✅ **VERIFICACIÓN POST-FIX:**

1. **Verificar permisos:**
   ```bash
   ls -la templates/us/es/onboarding/bienvenida.html
   # Debe mostrar: -rw-r--r-- (644)
   ```

2. **Probar la URL:**
   - Visitar: `https://www.egarage.cl/us/es/bienvenida/`
   - Debe cargar sin errores de permisos

3. **Verificar otros templates:**
   ```bash
   # Verificar que todos los templates globales tienen permisos correctos
   find templates -type f ! -perm 644
   # No debe mostrar ningún archivo
   
   # Verificar templates de apps
   find taller/templates -type f ! -perm 644 2>/dev/null
   # No debe mostrar ningún archivo
   ```

## 🛡️ **PREVENCIÓN FUTURA:**

### 1. Actualizar script de deployment

El script `scripts/deploy_to_server.sh` ahora incluye:
```bash
# Configurar permisos después de clonar
print_step "Configurando permisos..."
find . -type f -exec chmod 644 {} \;
find . -type d -exec chmod 755 {} \;
chmod 755 manage.py
print_success "Permisos configurados"
```

### 2. Verificar permisos en Git

Asegurarse de que los archivos en Git tengan permisos correctos:
```bash
# Localmente, antes de commitear
git config core.fileMode true
```

### 3. Configurar umask en el servidor

Agregar al `.bashrc` del usuario del servidor:
```bash
umask 022  # Archivos: 644, Directorios: 755
```

## 📋 **CHECKLIST DE VERIFICACIÓN:**

- [ ] Archivo `templates/us/es/onboarding/bienvenida.html` existe y tiene permisos `644`
- [ ] Archivo `taller/templates/taller/us/en/vehiculos/crear_vehiculo.html` existe y tiene permisos `644` (si aplica)
- [ ] Todos los templates globales tienen permisos `644` (archivos) y `755` (directorios)
- [ ] Todos los templates de apps tienen permisos `644` (archivos) y `755` (directorios)
- [ ] URL `/us/es/bienvenida/` carga correctamente
- [ ] URL `/us/vehiculos/crear/` carga correctamente
- [ ] No hay otros errores de permisos en logs

## 🔍 **DIAGNÓSTICO ADICIONAL:**

Si el problema persiste después de corregir permisos:

1. **Verificar usuario de uwsgi:**
   ```bash
   ps aux | grep uwsgi
   # Ver qué usuario ejecuta uwsgi
   ```

2. **Verificar ownership de archivos:**
   ```bash
   ls -la templates/us/es/onboarding/bienvenida.html
   # Verificar que el usuario de uwsgi puede leer el archivo
   ```

3. **Verificar SELinux/AppArmor (si aplica):**
   ```bash
   # En sistemas con SELinux
   getenforce
   # Si está en "Enforcing", puede necesitar ajustes
   ```

## 📞 **CONTACTO:**

Si el problema persiste después de seguir estos pasos, revisar:
- Logs de uwsgi: `/var/log/uwsgi/`
- Logs de Django: Configurados en `LOGGING` en settings.py
- Logs del servidor web: `/var/log/nginx/` o similar

