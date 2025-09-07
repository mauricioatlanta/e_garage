# ===============================================================
# 📋 GUÍA PASO A PASO - ACTUALIZACIÓN PYTHONANYWHERE
# ===============================================================
# Instrucciones detalladas para actualizar el servidor
# ===============================================================

## 🎯 OBJETIVO:
Arreglar el error 404 en las URLs de bienvenida subiendo los archivos actualizados.

## 📦 ARCHIVOS LISTOS EN TU PC:
✅ Directorio: `deploy_pythonanywhere/`
✅ ZIP: `egarage_update_20250724_154138.zip`

## 🚀 MÉTODO 1: UPLOAD MANUAL (RECOMENDADO - 5 MINUTOS)

### PASO 1: Acceder a PythonAnywhere
1. Ir a: https://www.pythonanywhere.com/
2. Login con tu cuenta: atlantareciclajes
3. Ir a la pestaña "Files"

### PASO 2: Navegar al directorio del proyecto
1. Ir a: `/home/atlantareciclajes/e-garage-atlantareciclajes/`
2. Verificar que estás en la carpeta correcta

### PASO 3: Actualizar URLs (CRÍTICO)
1. Ir a: `/home/atlantareciclajes/e-garage-atlantareciclajes/gestion_taller/`
2. **BACKUP:** Descargar el archivo `urls.py` actual (por seguridad)
3. **UPLOAD:** Subir `deploy_pythonanywhere/gestion_taller/urls.py`
4. **REEMPLAZAR:** Confirmar reemplazo del archivo existente

### PASO 4: Crear directorio templates (SI NO EXISTE)
1. Ir a: `/home/atlantareciclajes/e-garage-atlantareciclajes/templates/`
2. **CREAR:** Carpeta `onboarding/` (si no existe)
3. **ENTRAR:** a la carpeta `templates/onboarding/`

### PASO 5: Subir plantillas HTML
1. **UPLOAD:** `deploy_pythonanywhere/templates/onboarding/bienvenida_chile.html`
2. **UPLOAD:** `deploy_pythonanywhere/templates/onboarding/bienvenida_usa.html`
3. **VERIFICAR:** Que ambos archivos estén en la carpeta

### PASO 6: Recargar aplicación
1. Ir a la pestaña "Web"
2. Buscar: "atlantareciclajes.pythonanywhere.com"
3. **CLICK:** Botón "Reload atlantareciclajes.pythonanywhere.com"
4. **ESPERAR:** Confirmación "reloaded successfully"

### PASO 7: Verificar URLs
Probar estos enlaces en tu navegador:
- ✅ https://e-garage-atlantareciclajes.pythonanywhere.com/bienvenida/cl/
- ✅ https://e-garage-atlantareciclajes.pythonanywhere.com/bienvenida/usa/
- ✅ https://e-garage-atlantareciclajes.pythonanywhere.com/welcome/us/

## 🚀 MÉTODO 2: UPLOAD ZIP (ALTERNATIVO)

### PASO 1: Subir ZIP
1. Ir a PythonAnywhere → Files
2. Ir a: `/home/atlantareciclajes/`
3. **UPLOAD:** `egarage_update_20250724_154138.zip`

### PASO 2: Extraer ZIP
1. **CLICK:** En el archivo ZIP subido
2. **EXTRACT:** "Extract here"
3. **VERIFICAR:** Que se creó la carpeta con los archivos

### PASO 3: Mover archivos
1. **MOVER:** `gestion_taller/urls.py` → `/home/atlantareciclajes/e-garage-atlantareciclajes/gestion_taller/`
2. **CREAR:** `/home/atlantareciclajes/e-garage-atlantareciclajes/templates/onboarding/`
3. **MOVER:** Las plantillas HTML a la carpeta onboarding

### PASO 4: Recargar y verificar
1. Web → Reload
2. Probar URLs de bienvenida

## 🔧 ARCHIVOS INCLUIDOS EN EL PAQUETE:

### 📄 ARCHIVOS CRÍTICOS (OBLIGATORIOS):
- `gestion_taller/urls.py` - URLs con rutas de bienvenida
- `templates/onboarding/bienvenida_chile.html` - Página Chile 🇨🇱
- `templates/onboarding/bienvenida_usa.html` - Página USA 🇺🇸

### 📄 ARCHIVOS OPCIONALES (MEJORAS):
- `e_garage/settings_production.py` - Configuración optimizada
- `wsgi_production.py` - WSGI configurado
- `requirements.txt` - Dependencias actualizadas

## 🛠️ SOLUCIÓN DE PROBLEMAS:

### ❌ Error "File not found" al subir:
- Verificar que estás en la carpeta correcta
- Verificar permisos de escritura
- Intentar refrescar la página

### ❌ Error 500 después de reload:
1. Ir a Web → Error log
2. Buscar errores recientes
3. Verificar sintaxis en urls.py
4. Restaurar backup si es necesario

### ❌ URLs aún dan 404:
- Verificar que urls.py se subió correctamente
- Confirmar que las plantillas están en templates/onboarding/
- Verificar que ROOT_URLCONF apunta a gestion_taller.urls

### ❌ Plantillas no cargan:
- Verificar rutas exactas de archivos
- Confirmar que DEBUG = False en settings
- Verificar permisos de archivos

## 📊 VERIFICACIÓN FINAL:

### ✅ DESPUÉS DEL UPLOAD EXITOSO:
1. **URLs funcionan:** Sin error 404
2. **Páginas cargan:** Contenido correcto por país
3. **Diseño responsive:** Se ve bien en móvil
4. **Enlaces funcionan:** Navegación correcta

### 🎯 RESULTADO ESPERADO:
- **Chile:** Página en español con banderas y precios CLP
- **USA:** Página en inglés con banderas y precios USD
- **Navegación:** Enlaces al dashboard y registro funcionan

## 📞 CONTACTO DE EMERGENCIA:
Si tienes problemas durante el proceso:
1. **Error logs:** Web → Error log en PythonAnywhere
2. **Backup:** Restaurar urls.py original si hay problemas
3. **Support:** Contactar soporte de PythonAnywhere si es necesario

---
**⏱️ Tiempo estimado:** 5-10 minutos  
**🎯 Dificultad:** Fácil  
**✅ Éxito garantizado:** Si sigues los pasos exactos
