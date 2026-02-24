# 🚀 Cómo Actualizar el Servidor en PythonAnywhere

## 📋 Pasos para Actualizar los Cambios

### **Opción 1: Usando la Consola Bash (Recomendado - 5 minutos)**

1. **Acceder a PythonAnywhere:**
   - Ve a: https://www.pythonanywhere.com/
   - Inicia sesión con tu cuenta: `atlantareciclajes`
   - Ve a la pestaña **"Consoles"** → **"Bash"**

2. **Navegar al directorio del proyecto:**
   ```bash
   cd /home/atlantareciclajes/e_garage
   # O si está en otra ubicación:
   # cd /home/atlantareciclajes/apps/egarage
   ```

3. **Activar el entorno virtual:**
   ```bash
   workon venv_egarage310
   # O el nombre de tu venv:
   # source ~/.virtualenvs/venv_egarage310/bin/activate
   ```

4. **Obtener los últimos cambios de GitHub:**
   ```bash
   git pull origin main
   # Si estás en otra rama, usa:
   # git pull origin tu-rama
   ```

5. **Instalar dependencias (si hay cambios):**
   ```bash
   pip install -r requirements.txt
   ```

6. **Ejecutar migraciones (solo si hay cambios en modelos):**
   ```bash
   python manage.py migrate
   ```

7. **Recopilar archivos estáticos (IMPORTANTE para cambios en CSS/JS):**
   ```bash
   python manage.py collectstatic --noinput
   ```

8. **Recargar la aplicación:**
   - Ve a la pestaña **"Web"** en el dashboard
   - Busca tu aplicación: `atlantareciclajes.pythonanywhere.com`
   - Haz clic en el botón **"Reload atlantareciclajes.pythonanywhere.com"**
   - Espera el mensaje: "reloaded successfully"

---

### **Opción 2: Usando el Editor de Archivos (Si no tienes Git configurado)**

1. **Acceder a PythonAnywhere:**
   - Ve a: https://www.pythonanywhere.com/
   - Inicia sesión
   - Ve a la pestaña **"Files"**

2. **Navegar al archivo que necesitas actualizar:**
   - Ve a: `/home/atlantareciclajes/e_garage/templates/base.html`
   - O la ruta donde esté tu proyecto

3. **Editar el archivo:**
   - Haz clic en el archivo
   - Copia y pega el contenido actualizado
   - Guarda (Ctrl+S o botón Save)

4. **Recargar la aplicación:**
   - Ve a la pestaña **"Web"**
   - Haz clic en **"Reload"**

---

## ✅ Verificación Post-Actualización

1. **Abrir tu sitio en el navegador:**
   ```
   https://atlantareciclajes.pythonanywhere.com
   # O tu dominio personalizado
   ```

2. **Probar en móvil:**
   - Abre el sitio en un celular
   - Verifica que los botones de navegación muestren:
     - ⚙️ SETTINGS (o AJUSTES)
     - 👥 CLIENTS (o CLIENTES)
     - 🚗 VEHICLES (o VEHÍCULOS)
     - 🛠️ SERVICES (o SERVICIOS)
     - 🔧 PARTS (o REPUESTOS)
     - 🚪 LOGOUT (o SALIR)
     - 📄 DOCUMENTS (o DOCUMENTOS)

3. **Verificar que no hay errores:**
   - Ve a la pestaña **"Web"** → **"Error log"**
   - Verifica que no haya errores nuevos

---

## 🔧 Comandos Útiles

### Ver logs de errores:
```bash
# En la consola Bash:
tail -f /var/log/atlantareciclajes.pythonanywhere.com.error.log
```

### Verificar que el proyecto está actualizado:
```bash
cd /home/atlantareciclajes/e_garage
git log --oneline -5
```

### Limpiar caché de Python:
```bash
find . -type d -name "__pycache__" -exec rm -r {} +
find . -name "*.pyc" -delete
```

### Reiniciar manualmente (si el botón Reload no funciona):
```bash
touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py
```

---

## ⚠️ Solución de Problemas

### Si `git pull` falla:
```bash
# Verificar estado de Git
git status

# Si hay conflictos, hacer backup primero:
cp -r . ../backup_$(date +%Y%m%d_%H%M%S)

# Luego intentar pull de nuevo
git pull origin main
```

### Si `collectstatic` falla:
```bash
# Verificar permisos
ls -la staticfiles/

# Si hay problemas, limpiar primero:
rm -rf staticfiles/*
python manage.py collectstatic --noinput
```

### Si la aplicación no carga después de reload:
1. Verifica los logs de error en la pestaña "Web"
2. Verifica que todas las dependencias estén instaladas
3. Verifica que la base de datos esté accesible
4. Intenta reiniciar manualmente con `touch` al archivo WSGI

---

## 📝 Notas Importantes

- **Templates**: Los cambios en templates se reflejan inmediatamente (no necesitan migración)
- **CSS/JS**: Siempre ejecuta `collectstatic` después de cambios en archivos estáticos
- **Base de datos**: Solo ejecuta `migrate` si hay cambios en modelos
- **Tiempo de actualización**: Inmediato después de hacer "Reload"

---

## 🎯 Resumen Rápido

```bash
# 1. Consola Bash
cd /home/atlantareciclajes/e_garage
workon venv_egarage310
git pull origin main
python manage.py collectstatic --noinput

# 2. Dashboard → Web → Reload
```

¡Listo! 🎉







