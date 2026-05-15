# Archivos a Actualizar en Producción

## 📋 Lista de Archivos Críticos

Para solucionar el error 500 en el admin, debes actualizar estos **3 archivos** en el servidor de producción:

### 1. `whatsapp/admin.py`
**Ubicación:** `whatsapp/admin.py`  
**Cambios:** Manejo robusto de excepciones para evitar que errores en WhatsApp rompan el admin.

### 2. `whatsapp/apps.py`
**Ubicación:** `whatsapp/apps.py`  
**Cambios:** El método `ready()` ahora solo loggea errores en modo DEBUG.

### 3. `gestion_taller/urls.py`
**Ubicación:** `gestion_taller/urls.py`  
**Cambios:** La importación de `whatsapp.admin` ahora captura cualquier excepción.

---

## 🚀 Pasos para Actualizar

### Opción A: Usando Git (Recomendado)

Si tu servidor usa Git:

```bash
# En el servidor (PythonAnywhere Bash)
cd /home/tuusuario/mi_proyecto  # Ajusta la ruta
git pull origin main  # o master, según tu rama
```

### Opción B: Subir Archivos Manualmente

1. **Conecta a PythonAnywhere** (Files tab o SFTP)
2. **Sube estos 3 archivos** reemplazando los existentes:
   - `whatsapp/admin.py`
   - `whatsapp/apps.py`
   - `gestion_taller/urls.py`

### Opción C: Copiar y Pegar el Contenido

Si no puedes usar Git ni subir archivos, puedes editar directamente en PythonAnywhere:

1. Ve a **Files tab** en PythonAnywhere
2. Abre cada archivo y reemplaza su contenido con el contenido actualizado

---

## ✅ Después de Actualizar

**IMPORTANTE:** Después de actualizar los archivos, **reinicia el servidor web**:

1. Ve a la **Web tab** en PythonAnywhere
2. Haz clic en el botón **"Reload"** o **"Reload web app"**
3. Espera unos segundos
4. Prueba acceder a `https://www.egarage.cl/admin/`

---

## 🔍 Verificar que Funcionó

1. Accede a `https://www.egarage.cl/admin/`
2. Deberías ver el admin sin error 500
3. Si la app de WhatsApp está correctamente configurada, deberías ver "eGarage Air (WhatsApp)" en el menú lateral
4. Si no está configurada, el admin funcionará igual (no se romperá)

---

## 📝 Archivo Opcional (No Crítico)

Si quieres, también puedes subir:
- `DIAGNOSTICO_ERROR_500_PRODUCCION.md` (documentación de diagnóstico)

Este archivo NO es necesario para solucionar el error, solo es documentación.

---

## ⚠️ Si Aún Hay Problemas

Si después de actualizar los archivos y reiniciar el servidor aún hay error 500:

1. Revisa los logs de error en PythonAnywhere (Web tab → Error log)
2. Comparte el traceback completo
3. Verifica que los archivos se subieron correctamente (revisa las fechas de modificación)
