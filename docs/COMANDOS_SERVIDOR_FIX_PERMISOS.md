# Comandos para Ejecutar en el Servidor - Fix Permisos

## ✅ Verificar si los permisos ya están corregidos

```bash
# Verificar el archivo específico que está fallando
ls -la taller/templates/taller/us/en/vehiculos/crear_vehiculo.html

# Si muestra -rw-r--r-- (644), los permisos están correctos
# Si muestra algo diferente, ejecutar los comandos de abajo
```

## 🔧 Comandos para Corregir Permisos (Ejecutar uno por uno)

```bash
# 1. Ir al directorio actual
cd /home/atlantareciclajes/apps/egarage/current

# 2. Corregir permisos de templates de apps
find taller/templates -type f -exec chmod 644 {} \;
find taller/templates -type d -exec chmod 755 {} \;

# 3. Corregir permisos de templates globales
find templates -type f -exec chmod 644 {} \;
find templates -type d -exec chmod 755 {} \;

# 4. Verificar que se aplicaron correctamente
ls -la taller/templates/taller/us/en/vehiculos/crear_vehiculo.html

# 5. Recargar WSGI (si tienes permisos)
touch /var/www/www_atlantareciclajes_pythonanywhere_com_wsgi.py

# Si no tienes permisos para tocar el archivo WSGI, recarga desde el dashboard de PythonAnywhere
```

## 📋 Verificación Completa

```bash
# Verificar todos los templates con permisos incorrectos
find templates -type f ! -perm 644
find taller/templates -type f ! -perm 644

# Si no muestra nada, todos los permisos están correctos
```

## 🚨 Si el archivo no existe

Si el archivo `taller/templates/taller/us/en/vehiculos/crear_vehiculo.html` no existe, verifica la estructura:

```bash
# Ver qué templates de vehículos existen
find . -name "*crear_vehiculo*" -type f

# Ver estructura de templates
ls -la taller/templates/taller/us/en/vehiculos/ 2>/dev/null || echo "Directorio no existe"
ls -la templates/us/en/vehiculos/ 2>/dev/null || echo "Directorio no existe"
```










