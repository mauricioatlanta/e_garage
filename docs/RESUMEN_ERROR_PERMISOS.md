# Resumen: Error de Permisos en /us/es/bienvenida/

## 🚨 Problema

**Error:** `PermissionError: [Errno 13] Permission denied` al acceder a `/us/es/bienvenida/`

**Causa:** El proceso uwsgi no tiene permisos de lectura para el template `templates/us/es/onboarding/bienvenida.html`

## ✅ Solución Rápida (Ejecutar en el servidor)

```bash
# Conectarse al servidor
ssh atlantareciclajes@ssh.pythonanywhere.com

# Ir al release actual
cd /home/atlantareciclajes/apps/egarage/releases/2025-11-24_0525_eg

# Corregir permisos
find templates -type f -exec chmod 644 {} \;
find templates -type d -exec chmod 755 {} \;

# Recargar WSGI
touch /var/www/www_atlantareciclajes_pythonanywhere_com_wsgi.py
```

## 🔧 Solución Automática

Usar el script de corrección:

```bash
# En el servidor
cd /home/atlantareciclajes/apps/egarage/releases/2025-11-24_0525_eg
bash scripts/fix_permissions.sh
```

## 📋 Archivos Modificados

1. **`docs/SOLUCION_ERROR_PERMISOS_BIENVENIDA.md`** - Guía completa de solución
2. **`scripts/fix_permissions.sh`** - Script automático de corrección
3. **`scripts/deploy_to_server.sh`** - Actualizado para prevenir el problema en futuros deployments

## 🛡️ Prevención

El script de deployment ahora configura permisos automáticamente después de clonar el código, evitando este problema en futuros deployments.










