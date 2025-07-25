
# ===============================================================
# 🚀 COMANDOS DE UPLOAD PARA PYTHONANYWHERE
# ===============================================================

## 📂 ESTRUCTURA EN EL SERVIDOR:
/home/atlantareciclajes/e-garage-atlantareciclajes/

## 🔄 ARCHIVOS A SUBIR:

### 1. URLs principales (CRÍTICO)
   Subir: deploy_pythonanywhere/gestion_taller/urls.py
   Destino: /home/atlantareciclajes/e-garage-atlantareciclajes/gestion_taller/urls.py

### 2. Plantillas HTML (NUEVO)
   Crear directorio: /home/atlantareciclajes/e-garage-atlantareciclajes/templates/onboarding/
   Subir: deploy_pythonanywhere/templates/onboarding/bienvenida_chile.html
   Subir: deploy_pythonanywhere/templates/onboarding/bienvenida_usa.html

### 3. Configuración de producción (OPCIONAL)
   Subir: deploy_pythonanywhere/e_garage/settings_production.py
   Destino: /home/atlantareciclajes/e-garage-atlantareciclajes/e_garage/settings_production.py

### 4. WSGI y Requirements (OPCIONAL)
   Subir: deploy_pythonanywhere/wsgi_production.py
   Subir: deploy_pythonanywhere/requirements.txt

## ⚡ COMANDO RÁPIDO:
1. Subir SOLO urls.py y las 2 plantillas HTML
2. Web → Reload
3. Probar URLs: /bienvenida/cl/ y /bienvenida/usa/

## 🎯 URLs QUE FUNCIONARÁN:
✅ https://e-garage-atlantareciclajes.pythonanywhere.com/bienvenida/cl/
✅ https://e-garage-atlantareciclajes.pythonanywhere.com/bienvenida/usa/
✅ https://e-garage-atlantareciclajes.pythonanywhere.com/welcome/us/
