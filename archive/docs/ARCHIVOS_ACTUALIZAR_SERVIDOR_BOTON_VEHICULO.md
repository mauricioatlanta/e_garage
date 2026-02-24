# 📦 ARCHIVOS PARA ACTUALIZAR EN EL SERVIDOR
## Cambios: Botón "➕ New" Vehículo + Preselección Automática

### 📋 RESUMEN
Esta lista contiene todos los archivos modificados durante esta sesión para:
1. ✅ Corregir el error 404 al hacer clic en "➕ New" para crear vehículo
2. ✅ Preseleccionar automáticamente el cliente al crear vehículo
3. ✅ Preseleccionar automáticamente el vehículo recién creado al volver al documento

---

## 📁 ARCHIVOS A ACTUALIZAR (4 archivos)

### 1. **Templates - Formulario de Documento**
```
templates/taller/common/documentos/document_form.html
```
**Cambios realizados:**
- ✅ Botón de cliente cambiado de `<a>` a `<button>` (sin href)
- ✅ Script de navegación blindado para evitar error 404
- ✅ Función `cargarVehiculosPorCliente()` mejorada para aceptar vehículo a preseleccionar
- ✅ Nueva función `preseleccionarVehiculo()` con reintento automático
- ✅ Función `seleccionarCliente()` actualizada para detectar `new_vehiculo_id`
- ✅ Contexto `documentoData` actualizado con `prefillVehiculoId`

---

### 2. **Templates - Crear Vehículo (Chile)**
```
templates/cl/es/vehiculos/crear.html
```
**Cambios realizados:**
- ✅ Script de preselección de cliente con detección dinámica de país/idioma
- ✅ Fetch con headers AJAX (`X-Requested-With`, `Accept`)
- ✅ Manejo de formatos Select2 y array plano
- ✅ Manejo de errores mejorado con logging
- ✅ Inicialización de Select2 dentro del bloque correcto

---

### 3. **Vistas - Crear Vehículo (Country-Aware)**
```
taller/vehiculos/views_country_aware.py
```
**Cambios realizados:**
- ✅ Redirección mejorada después de crear vehículo
- ✅ Construcción de URL con `new_vehiculo_id` y mantenimiento de `cliente_id`
- ✅ Uso de `urllib.parse` para construir URL segura
- ✅ Guardado en sesión `prefill_vehiculo_id` para preselección alternativa

---

### 4. **Vistas - Crear Documento (Migrated)**
```
taller/documentos/views_migrated.py
```
**Cambios realizados:**
- ✅ Método `get_context_data()` actualizado
- ✅ Lectura de `prefill_vehiculo_id` desde sesión (`request.session`)
- ✅ Lectura de `new_vehiculo_id` desde URL (`request.GET`)
- ✅ Agregado `prefill_vehiculo_id` al contexto del template

---

## 🚀 COMANDOS PARA EJECUTAR EN EL SERVIDOR

Después de subir los archivos, ejecuta estos comandos en el servidor Linux:

```bash
# 1. Compilar mensajes de traducción (si hay cambios en i18n)
python manage.py compilemessages

# 2. Recopilar archivos estáticos
python manage.py collectstatic --noinput

# 3. Reiniciar Gunicorn (servidor de producción)
sudo systemctl restart gunicorn

# 4. Verificar que el servicio está corriendo
sudo systemctl status gunicorn
```

---

## ✅ VERIFICACIÓN POST-DEPLOYMENT

Después de actualizar, verifica que:

1. **Botón "➕ New" funciona:**
   - Ve a `/cl/documentos/form/`
   - Selecciona un cliente
   - Haz clic en "➕ New" (botón de vehículo)
   - Debe navegar a `/cl/es/vehiculos/crear/?next=...&cliente_id=X` (sin error 404)

2. **Cliente preseleccionado:**
   - Al llegar a la página de crear vehículo
   - El cliente seleccionado debe aparecer automáticamente en el campo "Cliente"

3. **Vehículo preseleccionado al volver:**
   - Crea un vehículo nuevo
   - Al volver al documento
   - El vehículo recién creado debe estar preseleccionado automáticamente

---

## 📝 NOTAS IMPORTANTES

- ⚠️ **No olvides hacer backup** antes de actualizar
- ⚠️ Los archivos de templates no requieren migraciones de base de datos
- ⚠️ Si usas caché (Redis/Memcached), considera limpiarlo después del deployment
- ⚠️ Verifica los logs del servidor después del reinicio: `sudo journalctl -u gunicorn -f`

---

## 🔍 ARCHIVOS RELACIONADOS (NO MODIFICADOS, pero relevantes)

Estos archivos NO fueron modificados, pero son parte del flujo:

- `taller/vehiculos/views_fbv.py` - Contiene `api_busqueda_clientes` (ya existía)
- `taller/vehiculos/forms.py` - Formulario de vehículo (no modificado en esta sesión)
- `taller/documentos/urls.py` - URLs de documentos (no modificado)

---

## 📅 FECHA DE CAMBIOS
**Sesión:** Botón Vehículo + Preselección Automática  
**Fecha:** Diciembre 2025  
**Archivos modificados:** 4 archivos

---

## 🆘 SI ALGO FALLA

1. **Error 404 al hacer clic en "➕ New":**
   - Verifica que `document_form.html` tiene el script de navegación actualizado
   - Revisa la consola del navegador (F12) para ver la URL generada
   - Verifica que la URL no incluya `/documentos/` en la ruta a vehículos

2. **Cliente no se preselecciona:**
   - Verifica que `crear.html` tiene el script de preselección actualizado
   - Revisa la consola del navegador para ver si hay errores en el fetch
   - Verifica que el endpoint `/cl/es/vehiculos/api/clientes/?id=X` funciona

3. **Vehículo no se preselecciona al volver:**
   - Verifica que `views_country_aware.py` está construyendo la URL con `new_vehiculo_id`
   - Verifica que `views_migrated.py` está leyendo `prefill_vehiculo_id` del contexto
   - Revisa la consola del navegador para ver si `new_vehiculo_id` está en la URL

---

**✅ Listo para deployment**

