# Comandos Rápidos: Fix Permisos Templates

## 🚀 Solución Rápida (Ejecutar en el servidor)

```bash
# Conectarse al servidor
ssh atlantareciclajes@ssh.pythonanywhere.com

# Ir al directorio actual (symlink)
cd /home/atlantareciclajes/apps/egarage/current

# O si prefieres un release específico:
# cd /home/atlantareciclajes/apps/egarage/releases/2025-11-24_0525_eg

# CORREGIR PERMISOS DE TODOS LOS TEMPLATES
# Templates globales
find templates -type f -exec chmod 644 {} \;
find templates -type d -exec chmod 755 {} \;

# Templates de apps (taller/templates/, etc.)
find taller/templates -type f -exec chmod 644 {} \; 2>/dev/null || true
find taller/templates -type d -exec chmod 755 {} \; 2>/dev/null || true

# Recargar WSGI
touch /var/www/www_atlantareciclajes_pythonanywhere_com_wsgi.py

# Verificar
ls -la templates/us/es/onboarding/bienvenida.html
ls -la taller/templates/taller/us/en/vehiculos/crear_vehiculo.html 2>/dev/null || echo "No encontrado"
```

## 🔧 Usar Script Automático

```bash
# En el servidor
cd /home/atlantareciclajes/apps/egarage/current
bash scripts/fix_permissions.sh
```

## ✅ Verificación Rápida

```bash
# Verificar permisos de templates específicos
stat -c "%a" templates/us/es/onboarding/bienvenida.html
stat -c "%a" taller/templates/taller/us/en/vehiculos/crear_vehiculo.html 2>/dev/null

# Debe mostrar: 644

# Verificar todos los templates con permisos incorrectos
find templates -type f ! -perm 644
find taller/templates -type f ! -perm 644 2>/dev/null
```

## 📝 Notas

- **644** = rw-r--r-- (lectura para todos, escritura solo para owner)
- **755** = rwxr-xr-x (ejecución para owner, lectura/ejecución para otros)
- El proceso uwsgi necesita permisos de lectura (644) en todos los templates









