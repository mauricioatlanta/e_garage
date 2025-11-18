# 🚀 INSTRUCCIONES PARA ACTUALIZAR EL SERVIDOR DE PRODUCCIÓN

## ⚠️ PROBLEMA ACTUAL
El servidor de producción (https://www.egarage.cl/) no muestra Colombia y Ecuador en el selector de países porque el archivo `templates/public/selector_pais.html` no estaba en el commit anterior.

## ✅ SOLUCIÓN APLICADA
Se ha agregado el archivo `templates/public/selector_pais.html` con Colombia y Ecuador al repositorio Git y se ha hecho push.

## 📋 PASOS PARA ACTUALIZAR EL SERVIDOR

### **OPCIÓN 1: Actualización Manual (Recomendado)**

1. **Conectar al servidor por SSH:**
   ```bash
   ssh atlantareciclajes@ssh.pythonanywhere.com
   ```

2. **Ir al directorio del proyecto:**
   ```bash
   cd /home/atlantareciclajes/apps/egarage
   # O si está en otra ubicación:
   cd ~/e_garage
   ```

3. **Actualizar desde Git:**
   ```bash
   git pull origin main
   ```

4. **Compilar traducciones (si es necesario):**
   ```bash
   python manage.py compilemessages --locale es
   ```

5. **Recolectar archivos estáticos (si hay cambios en CSS/JS):**
   ```bash
   python manage.py collectstatic --noinput
   ```

6. **Reiniciar la aplicación web:**
   ```bash
   touch /var/www/www_atlantareciclajes_pythonanywhere_com_wsgi.py
   ```
   
   **O desde el Dashboard de PythonAnywhere:**
   - Ir a: https://www.pythonanywhere.com/user/atlantareciclajes/webapps/
   - Hacer clic en "Reload" en la aplicación web

### **OPCIÓN 2: Usando el Script de Deployment**

Si tienes el script `deploy_to_server.sh` configurado:

```bash
./deploy_to_server.sh
```

---

## 🔍 VERIFICACIÓN POST-DEPLOYMENT

Después de actualizar, verifica:

1. **Ir a https://www.egarage.cl/**
2. **Verificar que aparezcan TODOS los países:**
   - 🇧🇷 Brasil
   - 🇨🇱 Chile
   - 🇨🇴 Colombia ← **DEBE APARECER**
   - 🇪🇨 Ecuador ← **DEBE APARECER**
   - 🇲🇽 México
   - 🇵🇪 Perú
   - 🇺🇸 United States
   - 🇻🇪 Venezuela

3. **Probar los enlaces:**
   - Hacer clic en Colombia → Debe ir a `/co/`
   - Hacer clic en Ecuador → Debe ir a `/ec/`

---

## 📝 ARCHIVOS ACTUALIZADOS

- ✅ `templates/public/selector_pais.html` - Agregados Colombia y Ecuador

---

## ⚡ COMANDO RÁPIDO (Todo en uno)

```bash
ssh atlantareciclajes@ssh.pythonanywhere.com "cd /home/atlantareciclajes/apps/egarage && git pull origin main && python manage.py compilemessages --locale es && python manage.py collectstatic --noinput && touch /var/www/www_atlantareciclajes_pythonanywhere_com_wsgi.py"
```

---

## 🆘 SOLUCIÓN DE PROBLEMAS

### Si Git pull falla:
```bash
# Verificar que estás en la rama correcta
git branch

# Si hay conflictos, hacer stash y pull
git stash
git pull origin main
git stash pop
```

### Si los cambios no se reflejan:
1. Limpiar caché del navegador (Ctrl+Shift+R o Cmd+Shift+R)
2. Verificar que el archivo se actualizó:
   ```bash
   cat templates/public/selector_pais.html | grep -i colombia
   ```
3. Reiniciar la aplicación web nuevamente

### Si hay errores de permisos:
```bash
# Verificar permisos
ls -la templates/public/selector_pais.html

# Si es necesario, ajustar permisos
chmod 644 templates/public/selector_pais.html
```

---

**Fecha:** $(Get-Date -Format "yyyy-MM-dd HH:mm")
**Commit:** Verificar con `git log --oneline -1`

