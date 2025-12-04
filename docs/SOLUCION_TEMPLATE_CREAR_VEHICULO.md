# Solución: Template crear_vehiculo.html no encontrado

## 🔍 Problema

Django busca el template en:
- `taller/templates/taller/us/en/vehiculos/crear_vehiculo.html`

Pero el archivo existe en:
- `templates/us/en/vehiculos/crear_vehiculo.html`

## ✅ Solución: Copiar archivo a la ruta correcta

Ejecutar estos comandos en el servidor:

```bash
cd /home/atlantareciclajes/apps/egarage/current

# 1. Crear la estructura de directorios si no existe
mkdir -p taller/templates/taller/us/en/vehiculos

# 2. Copiar el archivo desde templates/ a taller/templates/
cp templates/us/en/vehiculos/crear_vehiculo.html taller/templates/taller/us/en/vehiculos/crear_vehiculo.html

# 3. Dar permisos correctos
chmod 644 taller/templates/taller/us/en/vehiculos/crear_vehiculo.html
chmod 755 taller/templates/taller/us/en/vehiculos

# 4. Verificar que se copió correctamente
ls -la taller/templates/taller/us/en/vehiculos/crear_vehiculo.html

# 5. También copiar la versión en español si existe
mkdir -p taller/templates/taller/us/es/vehiculos
cp templates/us/es/vehiculos/crear_vehiculo.html taller/templates/taller/us/es/vehiculos/crear_vehiculo.html 2>/dev/null || echo "Versión ES no existe"
chmod 644 taller/templates/taller/us/es/vehiculos/crear_vehiculo.html 2>/dev/null || true

# 6. Corregir permisos de todos los templates de taller
find taller/templates -type f -exec chmod 644 {} \;
find taller/templates -type d -exec chmod 755 {} \;
```

## 🔧 Solución Alternativa: Corregir permisos de directorios bloqueados

Si hay muchos "Permission denied", primero corregir permisos de directorios:

```bash
cd /home/atlantareciclajes/apps/egarage/current

# Corregir permisos de directorios principales
chmod 755 templates
chmod 755 taller
chmod 755 taller/templates 2>/dev/null || true

# Luego intentar copiar el archivo
mkdir -p taller/templates/taller/us/en/vehiculos
cp templates/us/en/vehiculos/crear_vehiculo.html taller/templates/taller/us/en/vehiculos/crear_vehiculo.html
chmod 644 taller/templates/taller/us/en/vehiculos/crear_vehiculo.html
```

## 📋 Verificación

Después de copiar, verificar:

```bash
# Verificar que el archivo existe y tiene permisos correctos
ls -la taller/templates/taller/us/en/vehiculos/crear_vehiculo.html
# Debe mostrar: -rw-r--r-- (644)

# Verificar contenido (primeras líneas)
head -5 taller/templates/taller/us/en/vehiculos/crear_vehiculo.html
```

## 🚀 Recargar aplicación

Después de copiar el archivo, recargar la aplicación desde el dashboard de PythonAnywhere o ejecutar:

```bash
touch /var/www/www_atlantareciclajes_pythonanywhere_com_wsgi.py
```






