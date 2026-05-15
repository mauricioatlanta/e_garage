# 🚨 INSTRUCCIONES URGENTES - Actualizar Servidor

## ⚠️ PROBLEMA DETECTADO
Los cambios no se están viendo porque:
1. El servidor puede tener caché de templates
2. Los archivos estáticos pueden estar en caché
3. Necesitas limpiar la caché del navegador

## 📋 PASOS PARA RESOLVER

### 1. En el Servidor (PythonAnywhere):

```bash
# Conectarte a la consola Bash
cd /home/atlantareciclajes/apps/egarage/current

# Activar entorno virtual
workon venv_egarage310

# Obtener los últimos cambios
git pull origin main

# LIMPIAR CACHÉ DE TEMPLATES
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null
find . -name "*.pyc" -delete

# Recopilar archivos estáticos (IMPORTANTE)
python manage.py collectstatic --noinput --clear

# Recargar la aplicación
touch /var/www/www_atlantareciclajes_pythonanywhere_com_wsgi.py
```

### 2. En el Dashboard de PythonAnywhere:

1. Ve a: https://www.pythonanywhere.com/web_app_setup/
2. Busca tu aplicación
3. Haz clic en **"Reload"**
4. Espera confirmación

### 3. En tu Navegador (CELULAR):

**IMPORTANTE: Limpiar caché del navegador**

#### Android Chrome:
1. Abre Chrome
2. Menú (3 puntos) → Configuración
3. Privacidad y seguridad → Borrar datos de navegación
4. Selecciona "Imágenes y archivos en caché"
5. Borrar datos

#### iPhone Safari:
1. Configuración → Safari
2. Borrar historial y datos de sitios web

#### O usar modo incógnito:
- Abre el sitio en modo incógnito/privado para ver los cambios sin caché

### 4. Verificar que funcionó:

1. Abre: https://www.egarage.cl/us/vehiculos/
2. **En un celular**, verifica:
   - ✅ Los botones de navegación muestran texto claro (SETTINGS, CLIENTS, VEHICLES, etc.)
   - ✅ El botón "Add Vehicle" es visible y fácil de tocar
   - ✅ Los textos son legibles y no difusos

## 🔍 Si AÚN no funciona:

### Verificar que los archivos se actualizaron:

```bash
# En el servidor, verificar fecha de modificación
ls -la templates/base.html
ls -la templates/taller/us/en/vehiculos/lista_vehiculos.html

# Verificar contenido del CSS
grep -A 5 "FORZAR VISIBILIDAD" templates/base.html
```

### Forzar recarga completa:

```bash
# En el servidor
cd /home/atlantareciclajes/apps/egarage/current
rm -rf staticfiles/*
python manage.py collectstatic --noinput
touch /var/www/www_atlantareciclajes_pythonanywhere_com_wsgi.py
```

### Verificar logs de errores:

En PythonAnywhere Dashboard → Web → Error log
Verifica que no haya errores de CSS o templates

## 📝 Archivos Modificados:

1. `templates/base.html` - Estilos mejorados para botones de navegación
2. `templates/taller/us/en/vehiculos/lista_vehiculos.html` - Botón Add Vehicle visible en móviles
3. `templates/taller/us/en/vehiculos/vehiculo_list.html` - Botón Add Vehicle visible en móviles

## ✅ Checklist Final:

- [ ] Git pull ejecutado
- [ ] Caché de templates limpiada
- [ ] collectstatic ejecutado con --clear
- [ ] Aplicación recargada (touch WSGI o botón Reload)
- [ ] Caché del navegador limpiada
- [ ] Probado en celular real (no solo emulador)
- [ ] Verificado que los textos se ven claros

---

**Si después de todos estos pasos aún no funciona, puede ser un problema de configuración del servidor o de caché a nivel de CDN/proxy.**







