# 🔧 ACTUALIZAR SERVIDOR - Búsqueda de Clientes

## 📋 Archivos a Actualizar

### ⚠️ **IMPORTANTE: Error Crítico en Servidor**

Antes de actualizar los archivos de búsqueda, **DEBES** solucionar este error primero:

**Error**: `ModuleNotFoundError: No module named 'taller.configuracion'`

**Solución**: Ver documento **`SOLUCION_MODULO_CONFIGURACION_FALTANTE.md`** para instrucciones detalladas.

**Resumen rápido**: Subir el directorio completo `taller/configuracion/` con 3 archivos:
- `__init__.py`
- `rubros_logic.py`
- `rubros_responsables.py`

---

### Archivos Modificados (Búsqueda de Clientes)

Se corrigió el problema de búsqueda de clientes en `/us/vehiculos/crear/`. Los siguientes archivos necesitan actualizarse en el servidor:

### 1. **taller/vehiculos/forms.py**
   - **Cambio**: Mejora en la generación de URL del autocomplete con prefijo de país
   - **Ubicación en servidor**: `taller/vehiculos/forms.py`

### 2. **templates/us/es/vehiculos/crear_vehiculo.html**
   - **Cambio**: Mejora en JavaScript para corregir URL del autocomplete
   - **Ubicación en servidor**: `templates/us/es/vehiculos/crear_vehiculo.html`

### 3. **taller/vehiculos/views_fbv.py** (Opcional)
   - **Cambio**: Mejora en manejo de errores (VIN duplicado)
   - **Ubicación en servidor**: `taller/vehiculos/views_fbv.py`

---

## 🚀 INSTRUCCIONES DE ACTUALIZACIÓN

### **OPCIÓN 1: Upload Manual (Recomendado - 5 minutos)**

#### Paso 1: Acceder al servidor
1. Conectarse al servidor (SSH, FTP, o panel de control)
2. Navegar al directorio raíz del proyecto

#### Paso 2: Hacer backup (Opcional pero recomendado)
```bash
# Backup del formulario
cp taller/vehiculos/forms.py taller/vehiculos/forms.py.backup_$(date +%Y%m%d_%H%M%S)

# Backup del template
cp templates/us/es/vehiculos/crear_vehiculo.html templates/us/es/vehiculos/crear_vehiculo.html.backup_$(date +%Y%m%d_%H%M%S)
```

#### Paso 3: Solucionar error crítico PRIMERO
**⚠️ HACER ESTO PRIMERO** - Ver `SOLUCION_MODULO_CONFIGURACION_FALTANTE.md`

1. Crear directorio `taller/configuracion/` en el servidor
2. Subir los 3 archivos del módulo configuracion:
   - `__init__.py`
   - `rubros_logic.py`
   - `rubros_responsables.py`
3. Recargar y verificar que el error `ModuleNotFoundError` desaparece

#### Paso 4: Subir archivos actualizados
1. **Subir `taller/vehiculos/forms.py`**
   - Desde tu PC: `taller/vehiculos/forms.py`
   - Al servidor: `taller/vehiculos/forms.py`
   - Reemplazar el archivo existente

2. **Subir `templates/us/es/vehiculos/crear_vehiculo.html`**
   - Desde tu PC: `templates/us/es/vehiculos/crear_vehiculo.html`
   - Al servidor: `templates/us/es/vehiculos/crear_vehiculo.html`
   - Reemplazar el archivo existente

3. **Subir `taller/vehiculos/views_fbv.py`** (Opcional - mejora de errores)
   - Desde tu PC: `taller/vehiculos/views_fbv.py`
   - Al servidor: `taller/vehiculos/views_fbv.py`
   - Reemplazar el archivo existente

#### Paso 5: Recargar aplicación
- Si usas PythonAnywhere: Ir a pestaña "Web" → Click "Reload"
- Si usas otro servidor: Reiniciar el servicio Django/Gunicorn/uWSGI
- Si usas Docker: `docker-compose restart` o reiniciar contenedor

#### Paso 6: Limpiar cache (Opcional)
```bash
# Limpiar cache de Python
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete

# Si usas collectstatic
python manage.py collectstatic --noinput
```

#### Paso 7: Verificar
1. Ir a: `https://www.egarage.cl/us/vehiculos/crear/`
2. Abrir la consola del navegador (F12)
3. Intentar buscar un cliente escribiendo en el campo "Cliente"
4. Verificar que aparezcan los logs en consola y que la búsqueda funcione

---

### **OPCIÓN 2: Git Pull (Si usas Git en servidor)**

```bash
# Conectarse al servidor
ssh usuario@servidor

# Ir al directorio del proyecto
cd /ruta/al/proyecto

# Hacer pull de los cambios
git pull origin main  # o la rama que uses

# Recargar aplicación
# (depende de tu configuración)
systemctl restart gunicorn
# o
docker-compose restart
# o en PythonAnywhere: Reload en pestaña Web
```

---

### **OPCIÓN 3: SCP/SFTP (Línea de comandos)**

```bash
# Desde tu PC, subir los archivos
scp taller/vehiculos/forms.py usuario@servidor:/ruta/al/proyecto/taller/vehiculos/forms.py
scp templates/us/es/vehiculos/crear_vehiculo.html usuario@servidor:/ruta/al/proyecto/templates/us/es/vehiculos/crear_vehiculo.html

# Luego conectarse al servidor y recargar
ssh usuario@servidor
cd /ruta/al/proyecto
# Recargar aplicación según tu configuración
```

---

## ✅ VERIFICACIÓN POST-ACTUALIZACIÓN

### 1. Verificar que los archivos se actualizaron
```bash
# En el servidor, verificar fecha de modificación
ls -lh taller/vehiculos/forms.py
ls -lh templates/us/es/vehiculos/crear_vehiculo.html
```

### 2. Probar la funcionalidad
1. Ir a: `https://www.egarage.cl/us/vehiculos/crear/`
2. Abrir consola del navegador (F12 → Console)
3. Escribir en el campo "Cliente"
4. Deberías ver logs como:
   - `🔍 Verificando campo cliente:`
   - `🔧 URL de autocomplete corregida:` o `✅ URL de autocomplete ya tiene prefijo correcto:`
   - `✅ Select2 inicializado correctamente por DAL`

### 3. Verificar que la búsqueda funciona
- Escribir al menos 1 carácter en el campo "Cliente"
- Deberían aparecer resultados de clientes
- Si no aparecen, revisar los logs en consola para identificar el problema

---

## 🐛 SOLUCIÓN DE PROBLEMAS

### Problema: La búsqueda sigue sin funcionar
1. **Verificar logs en consola del navegador**
   - Buscar errores en rojo
   - Verificar que la URL del autocomplete tenga el prefijo `/us/`

2. **Verificar que los archivos se subieron correctamente**
   ```bash
   # En el servidor
   grep -n "data-ajax--url" templates/us/es/vehiculos/crear_vehiculo.html
   grep -n "absolute_url" taller/vehiculos/forms.py
   ```

3. **Limpiar cache del navegador**
   - Ctrl+Shift+R (hard refresh)
   - O abrir en modo incógnito

4. **Verificar que el servidor recargó los cambios**
   - Reiniciar el servicio nuevamente
   - Verificar logs del servidor para errores

### Problema: Error 404 en la URL del autocomplete
- Verificar que la URL generada sea: `/us/vehiculos/autocomplete/cliente/`
- Verificar que la ruta existe en `taller/vehiculos/urls.py`

### Problema: Los cambios no se reflejan
- Asegurarse de que se recargó la aplicación
- Limpiar cache de Python (`__pycache__`)
- Verificar que se subieron los archivos correctos

---

## 📝 RESUMEN DE CAMBIOS

### En `taller/vehiculos/forms.py`:
- ✅ Generación de URL absoluta con prefijo de país
- ✅ Establecimiento de `data-ajax--url` como fallback
- ✅ Logging mejorado para depuración

### En `templates/us/es/vehiculos/crear_vehiculo.html`:
- ✅ Corrección automática de URL del autocomplete
- ✅ Verificación de múltiples atributos donde DAL puede poner la URL
- ✅ Logging detallado en consola
- ✅ Fallback manual de Select2 si DAL no funciona

---

## 🎯 RESULTADO ESPERADO

Después de actualizar estos archivos:
- ✅ La búsqueda de clientes funciona en `/us/vehiculos/crear/`
- ✅ La URL del autocomplete incluye el prefijo `/us/` correctamente
- ✅ Los logs en consola muestran el proceso de inicialización
- ✅ Los clientes aparecen al escribir en el campo de búsqueda

---

**Fecha de creación**: 2025-11-25
**Archivos modificados**: 2
**Tiempo estimado de actualización**: 5-10 minutos

