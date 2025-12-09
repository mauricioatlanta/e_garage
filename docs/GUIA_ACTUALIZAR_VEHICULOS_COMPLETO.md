# 🔧 GUÍA: Actualizar Módulo Vehículos Completo en el Servidor

## 🎯 Problema Identificado

Después de actualizar los templates, se detectaron dos problemas:
1. **Los modelos no se cargan** al seleccionar una marca en el servidor
2. **Las marcas son diferentes** entre servidor y PC local

## 🔍 Causas Identificadas

### 1. Vista `ajax_modelos_por_marca_anio` no filtra por país
- **Archivo:** `taller/vehiculos/views_fbv.py`
- **Problema:** La función no filtra por `country`, trayendo modelos de todos los países
- **Solución:** Agregar filtro por país del usuario

### 2. Archivos estáticos (JavaScript) no actualizados
- **Archivo:** `static/js/formulario_jerarquico.js`
- **Problema:** El servidor puede tener una versión antigua del JavaScript
- **Solución:** Subir el archivo actualizado

### 3. Diferencias en la base de datos
- **Problema:** Las marcas en el servidor son diferentes a las de tu PC
- **Causa:** Bases de datos independientes con datos diferentes
- **Solución:** Sincronizar marcas o verificar que se crean automáticamente

---

## 📋 ARCHIVOS A ACTUALIZAR

### 1. Archivos Python (Backend)
```
taller/vehiculos/views_fbv.py          ← CRÍTICO: Corregir filtro por país
taller/vehiculos/urls.py              ← Verificar URLs
taller/vehiculos/forms.py             ← Verificar formularios
```

### 2. Archivos JavaScript (Frontend)
```
static/js/formulario_jerarquico.js    ← CRÍTICO: JavaScript jerárquico
```

### 3. Templates HTML
```
templates/cl/es/vehiculos/crear.html  ← Ya actualizado
templates/cl/es/vehiculos/editar.html ← Si existe
```

---

## ⚡ PASOS PARA ACTUALIZAR

### PASO 1: Actualizar Vista Backend (CRÍTICO)

**Archivo:** `taller/vehiculos/views_fbv.py`

Busca la función `ajax_modelos_por_marca_anio` (alrededor de línea 891) y asegúrate de que tenga:

```python
@require_GET
@login_required
def ajax_modelos_por_marca_anio(request, *args, **kwargs):
    """
    Devuelve los modelos para una marca dada.
    IMPORTANTE: Filtra por país del usuario para multi-tenant.
    """
    marca_id = request.GET.get("marca_id") or request.GET.get("marca")
    anio = request.GET.get("anio") or request.GET.get("year")

    if not marca_id:
        return JsonResponse({"results": []})

    # Filtrar por país del usuario (multi-tenant)
    country = _get_country(request)
    qs = Modelo.objects.filter(marca_id=marca_id, country=country).order_by("nombre")

    data = [{"id": m.id, "text": str(m)} for m in qs]
    return JsonResponse({"results": data})
```

**Verificar que:**
- ✅ Tiene `country = _get_country(request)`
- ✅ El filtro incluye `.filter(marca_id=marca_id, country=country)`

---

### PASO 2: Subir Archivo JavaScript

**Archivo:** `static/js/formulario_jerarquico.js`

**Método FileZilla:**
1. Conecta a: `atlantareciclajes.pythonanywhere.com` (SFTP, puerto 22)
2. Navega a:
   - **Remoto:** `/home/atlantareciclajes/apps/egarage/current/static/js/`
   - **Local:** `E:\projecto\e_garage\static\js\`
3. Arrastra `formulario_jerarquico.js` del local al remoto
4. Verifica permisos: `644`

**Método SCP (PowerShell):**
```powershell
cd E:\projecto\e_garage
scp static\js\formulario_jerarquico.js atlantareciclajes@atlantareciclajes.pythonanywhere.com:/home/atlantareciclajes/apps/egarage/current/static/js/formulario_jerarquico.js
```

---

### PASO 3: Subir Vista Corregida

**Archivo:** `taller/vehiculos/views_fbv.py`

**Método FileZilla:**
1. Navega a:
   - **Remoto:** `/home/atlantareciclajes/apps/egarage/current/taller/vehiculos/`
   - **Local:** `E:\projecto\e_garage\taller\vehiculos\`
2. Arrastra `views_fbv.py` del local al remoto
3. Verifica permisos: `644`

**Método SCP:**
```powershell
scp taller\vehiculos\views_fbv.py atlantareciclajes@atlantareciclajes.pythonanywhere.com:/home/atlantareciclajes/apps/egarage/current/taller/vehiculos/views_fbv.py
```

---

### PASO 4: Recargar Aplicación en el Servidor

Después de subir los archivos Python, necesitas recargar la aplicación:

**Opción A: Desde el Dashboard de PythonAnywhere**
1. Ve a: https://www.pythonanywhere.com/user/atlantareciclajes/webapps/
2. Click en **"Reload"** en tu aplicación

**Opción B: Desde SSH**
```bash
ssh atlantareciclajes@atlantareciclajes.pythonanywhere.com
touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py
# O si usas Gunicorn:
sudo systemctl restart gunicorn
```

---

### PASO 5: Limpiar Caché del Navegador

1. Abre: https://www.egarage.cl/cl/es/vehiculos/crear/
2. Presiona `Ctrl+Shift+Delete`
3. Selecciona "Imágenes y archivos en caché"
4. Click en "Borrar datos"
5. Recarga la página con `Ctrl+F5`

---

## 🔍 VERIFICACIÓN

### 1. Verificar que los modelos se cargan

1. Abre: https://www.egarage.cl/cl/es/vehiculos/crear/
2. Abre la consola del navegador (`F12` → Console)
3. Selecciona una marca
4. Deberías ver en la consola:
   ```
   🔧 cargarModelos() llamado: {marcaId: "1", year: "2024", modelosUrl: "..."}
   📤 URL de modelos: /cl/es/vehiculos/ajax/modelos-por-marca-anio/?marca_id=1&anio=2024
   📥 Respuesta recibida: 200 OK
   📦 Datos recibidos: {results: [...]}
   ✅ X modelo(s) encontrado(s)
   ```

### 2. Verificar que las marcas son correctas

1. En la misma página, verifica que las marcas mostradas corresponden a Chile
2. Si faltan marcas, el sistema debería crearlas automáticamente (ver `api_marcas` en `views_fbv.py`)

### 3. Verificar endpoint AJAX directamente

Abre en el navegador (después de iniciar sesión):
```
https://www.egarage.cl/cl/es/vehiculos/ajax/modelos-por-marca-anio/?marca_id=1&anio=2024
```

Deberías ver un JSON con `{"results": [...]}`

---

## 🆘 SOLUCIÓN DE PROBLEMAS

### Problema: Los modelos aún no se cargan

**Verificaciones:**
1. **Consola del navegador:** ¿Hay errores JavaScript?
   - Si hay errores 404, verifica que las URLs estén correctas
   - Si hay errores 403, verifica que estés logueado

2. **Network tab:** ¿La petición AJAX se está haciendo?
   - Abre `F12` → Network
   - Filtra por "XHR"
   - Selecciona una marca
   - Deberías ver una petición a `/ajax/modelos-por-marca-anio/`
   - Verifica el status code (debe ser 200)

3. **Respuesta del servidor:**
   - Click en la petición AJAX
   - Ve a la pestaña "Response"
   - Deberías ver `{"results": [...]}`

**Soluciones:**
- Si el status es 404: Verifica que `taller/vehiculos/urls.py` tenga la ruta correcta
- Si el status es 500: Revisa los logs del servidor
- Si el status es 200 pero no hay resultados: Verifica que haya modelos en la BD para esa marca/país

### Problema: Las marcas siguen siendo diferentes

**Causa:** Bases de datos diferentes entre servidor y PC local

**Soluciones:**

**Opción A: Sincronizar marcas manualmente**
```python
# En el servidor, ejecuta en Django shell:
python manage.py shell

from taller.models.marca import Marca
from django.contrib.auth.models import User

# Obtener usuario/empresa
user = User.objects.first()
empresa = user.empresa
pais = empresa.pais

# Verificar marcas existentes
marcas = Marca.objects.filter(country=pais)
print(f"Marcas en servidor: {marcas.count()}")

# Si no hay marcas, se crearán automáticamente al acceder a api_marcas
```

**Opción B: Crear marcas desde el admin**
1. Ve a: https://www.egarage.cl/admin/
2. Navega a: `Taller → Marcas`
3. Crea las marcas necesarias para Chile

**Opción C: Usar el endpoint automático**
- El sistema crea marcas automáticamente si no existen (ver `api_marcas` en `views_fbv.py`)
- Solo necesitas acceder a la página de crear vehículo

### Problema: Error 500 en el servidor

**Verificar logs:**
```bash
ssh atlantareciclajes@atlantareciclajes.pythonanywhere.com
tail -f /var/log/atlantareciclajes.pythonanywhere.com.error.log
```

**Causas comunes:**
- Error de sintaxis en `views_fbv.py`
- Import faltante (ej: `_get_country` no está definido)
- Error en la base de datos

**Solución:**
1. Verifica que `_get_country` esté definido en `views_fbv.py`
2. Verifica que no haya errores de sintaxis
3. Revisa los logs para el error específico

---

## ✅ CHECKLIST FINAL

Después de actualizar, verifica:

- [ ] `taller/vehiculos/views_fbv.py` tiene filtro por país en `ajax_modelos_por_marca_anio`
- [ ] `static/js/formulario_jerarquico.js` está actualizado en el servidor
- [ ] `templates/cl/es/vehiculos/crear.html` está actualizado
- [ ] Aplicación recargada en PythonAnywhere
- [ ] Caché del navegador limpiada
- [ ] Los modelos se cargan al seleccionar una marca
- [ ] Las marcas mostradas son correctas para Chile
- [ ] No hay errores en la consola del navegador
- [ ] El endpoint AJAX responde correctamente

---

## 📝 RESUMEN RÁPIDO

**Archivos críticos a subir:**
1. `taller/vehiculos/views_fbv.py` (corregir filtro por país)
2. `static/js/formulario_jerarquico.js` (JavaScript actualizado)
3. `templates/cl/es/vehiculos/crear.html` (ya actualizado)

**Comandos rápidos:**
```powershell
# Subir JavaScript
scp static\js\formulario_jerarquico.js atlantareciclajes@atlantareciclajes.pythonanywhere.com:/home/atlantareciclajes/apps/egarage/current/static/js/

# Subir vista Python
scp taller\vehiculos\views_fbv.py atlantareciclajes@atlantareciclajes.pythonanywhere.com:/home/atlantareciclajes/apps/egarage/current/taller/vehiculos/
```

**Después de subir:**
1. Recargar aplicación en PythonAnywhere
2. Limpiar caché del navegador
3. Verificar que funciona

---

**¡Actualización completada!** 🎉











