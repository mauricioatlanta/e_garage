# 🚀 INSTRUCCIONES DE DEPLOYMENT - eGarage

## 📋 Cambios Realizados en Esta Sesión

### 1. **Traducciones de Botones de Navegación**
- ✅ Actualizado `templates/base.html` para usar `{% trans %}` en todos los botones de navegación
- ✅ Agregadas traducciones al archivo `locale/es/LC_MESSAGES/django.po`
- ✅ Compiladas las traducciones con `python manage.py compilemessages --locale es`

### 2. **Filtrado de Mensajes en Login**
- ✅ Filtrados mensajes de Django que contienen:
  - "Successfully signed in"
  - "You have signed out"
  - "Professional Automotive Management System"
- ✅ Actualizados templates:
  - `templates/account/login.html`
  - `templates/taller/us/en/account/login.html`
  - `templates/taller/cl/es/account/login.html`

---

## 🚀 PASOS PARA DEPLOYMENT

### **PASO 1: Preparación Local (Ya Completado)**
```bash
# ✅ Traducciones compiladas
python manage.py compilemessages --locale es
```

### **PASO 2: Subir Archivos al Servidor**

**Opción A: Usando Git (Recomendado)**
```bash
# En tu máquina local:
git add .
git commit -m "Actualización: traducciones de navegación y filtrado de mensajes login"
git push origin main

# En el servidor (PythonAnywhere):
cd ~/e_garage  # o la ruta donde tengas el proyecto
git pull origin main
```

**Opción B: Usando SCP (Windows PowerShell)**
```powershell
# Subir archivos específicos
scp templates/base.html usuario@ssh.pythonanywhere.com:~/e_garage/templates/
scp templates/account/login.html usuario@ssh.pythonanywhere.com:~/e_garage/templates/account/
scp templates/taller/us/en/account/login.html usuario@ssh.pythonanywhere.com:~/e_garage/templates/taller/us/en/account/
scp templates/taller/cl/es/account/login.html usuario@ssh.pythonanywhere.com:~/e_garage/templates/taller/cl/es/account/
scp locale/es/LC_MESSAGES/django.mo usuario@ssh.pythonanywhere.com:~/e_garage/locale/es/LC_MESSAGES/
```

**Opción C: Usando FileZilla/WinSCP**
- Conectar al servidor
- Subir los archivos modificados a sus respectivas ubicaciones

---

### **PASO 3: Comandos en el Servidor (PythonAnywhere)**

**Conectar al servidor:**
```bash
# SSH a PythonAnywhere
ssh usuario@ssh.pythonanywhere.com
```

**Ejecutar en el servidor:**
```bash
# 1. Ir al directorio del proyecto
cd ~/e_garage  # o la ruta donde tengas el proyecto

# 2. Activar virtualenv (si usas uno)
workon venv_egarage  # o: source venv/bin/activate

# 3. Compilar traducciones (si no las subiste compiladas)
python manage.py compilemessages --locale es

# 4. Recolectar archivos estáticos (si hay cambios en CSS/JS)
python manage.py collectstatic --noinput

# 5. Verificar que todo esté bien
python manage.py check

# 6. Reiniciar la aplicación web
# En PythonAnywhere, ve al Dashboard → Web → Reload
# O ejecuta:
touch /var/www/usuario_pythonanywhere_com_wsgi.py
```

---

## 📝 Archivos Modificados

### Templates:
- `templates/base.html` - Botones de navegación con traducciones
- `templates/account/login.html` - Filtrado de mensajes
- `templates/taller/us/en/account/login.html` - Filtrado de mensajes
- `templates/taller/cl/es/account/login.html` - Filtrado de mensajes

### Traducciones:
- `locale/es/LC_MESSAGES/django.po` - Nuevas traducciones agregadas
- `locale/es/LC_MESSAGES/django.mo` - Archivo compilado (generado)

---

## ✅ Verificación Post-Deployment

Después del deployment, verifica:

1. **Botones de navegación traducidos:**
   - Ir a cualquier página del sistema
   - Cambiar idioma a español
   - Verificar que los botones muestren texto en español

2. **Mensajes de login filtrados:**
   - Ir a `/accounts/login/`
   - Verificar que NO aparezcan:
     - "Successfully signed in as..."
     - "You have signed out"
     - "Professional Automotive Management System"

3. **Funcionalidad general:**
   - Probar login
   - Probar cambio de idioma
   - Navegar por las diferentes secciones

---

## 🔧 Solución de Problemas

### Si las traducciones no funcionan:
```bash
# En el servidor:
python manage.py compilemessages --locale es
python manage.py collectstatic --noinput
# Reiniciar web app
```

### Si hay errores de sintaxis:
```bash
python manage.py check
```

### Si los cambios no se reflejan:
- Verificar que los archivos se subieron correctamente
- Limpiar caché del navegador
- Reiniciar la aplicación web en PythonAnywhere

---

## 📞 Soporte

Si encuentras algún problema durante el deployment, verifica:
1. ✅ Que todos los archivos se subieron correctamente
2. ✅ Que las traducciones están compiladas (`django.mo` existe)
3. ✅ Que el servidor web se reinició
4. ✅ Que no hay errores en los logs del servidor

---

**Fecha de deployment:** $(date +%Y-%m-%d)
**Versión:** 2.0.x

