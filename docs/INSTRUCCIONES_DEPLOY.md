
# ===============================================================
# 🚀 INSTRUCCIONES DE ACTUALIZACIÓN PARA PYTHONANYWHERE
# ===============================================================

## 🎯 PROBLEMA IDENTIFICADO:
El error 404 en /bienvenida/usa/ se debe a que las URLs nuevas 
no están en el servidor de producción.

## 📦 ARCHIVOS A SUBIR:

### 1. 📂 gestion_taller/urls.py (ACTUALIZAR)
   - Contiene las nuevas rutas de bienvenida
   - Reemplazar el archivo existente en el servidor

### 2. 📂 templates/onboarding/bienvenida_chile.html (NUEVO)
   - Plantilla para la página de bienvenida de Chile
   - Crear en: /templates/onboarding/

### 3. 📂 templates/onboarding/bienvenida_usa.html (NUEVO)
   - Plantilla para la página de bienvenida de USA
   - Crear en: /templates/onboarding/

## 🚀 PASOS DE ACTUALIZACIÓN:

### PASO 1: Subir archivos via Files
1. Ir a "Files" en PythonAnywhere
2. Navegar a: /home/atlantareciclajes/e-garage-atlantareciclajes/
3. Subir y reemplazar: gestion_taller/urls.py
4. Crear directorio: templates/onboarding/ (si no existe)
5. Subir: bienvenida_chile.html y bienvenida_usa.html

### PASO 2: Recargar aplicación web
1. Ir al tab "Web"
2. Hacer clic en "Reload atlantareciclajes.pythonanywhere.com"

### PASO 3: Verificar URLs
Probar estos enlaces:
✅ https://e-garage-atlantareciclajes.pythonanywhere.com/bienvenida/cl/
✅ https://e-garage-atlantareciclajes.pythonanywhere.com/bienvenida/usa/
✅ https://e-garage-atlantareciclajes.pythonanywhere.com/welcome/us/

## 🎉 RESULTADO ESPERADO:
Después de estos pasos, las URLs de bienvenida funcionarán correctamente.

## 📞 SOPORTE:
Si hay problemas, verificar en "Error log" del tab Web.
