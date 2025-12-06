# 🔍 Verificar Actualización en el Servidor

## ⚠️ Problema

El enlace "Recordatorios de Mantenimiento" no aparece en `/reportes/` en el servidor.

---

## ✅ Solución Paso a Paso

### 1. Verificar que el Código se Actualizó

```bash
# En el servidor
cd /ruta/al/proyecto/e_garage

# Ver el último commit
git log --oneline -1
# Debe mostrar: "Implementación completa: Sistema de Kilometraje..."

# Si NO muestra ese commit, hacer pull:
git pull origin main
```

### 2. Verificar que el Template Tiene el Enlace

```bash
# Buscar el enlace en el template
grep -n "kilometraje/recordatorios" templates/taller/reportes/reportes.html

# Debe mostrar algo como:
# 359:        <a href="kilometraje/recordatorios/" class="reporte-card">
```

### 3. Si el Template NO Tiene el Enlace

```bash
# Forzar actualización del archivo
git checkout HEAD -- templates/taller/reportes/reportes.html

# O descargar específicamente ese archivo
git show HEAD:templates/taller/reportes/reportes.html > templates/taller/reportes/reportes.html
```

### 4. Limpiar Cache de Templates (CRÍTICO)

```bash
# Django cachea los templates, hay que limpiar:
python manage.py shell
# En el shell:
>>> from django.core.cache import cache
>>> cache.clear()
>>> exit()
```

### 5. Limpiar Cache de Python

```bash
# Eliminar archivos .pyc
find . -type f -name "*.pyc" -delete
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null

# Específicamente en templates
find templates -type f -name "*.pyc" -delete
```

### 6. Reiniciar el Servidor (MUY IMPORTANTE)

```bash
# El servidor DEBE reiniciarse para cargar los nuevos templates
sudo systemctl restart gunicorn
# o
sudo systemctl restart uwsgi
# o
sudo systemctl restart apache2
```

### 7. Verificar que el Archivo Existe en el Servidor

```bash
# Verificar que el template existe y tiene el contenido correcto
cat templates/taller/reportes/reportes.html | grep -A 5 "Recordatorios de Mantenimiento"

# Debe mostrar:
# <!-- Recordatorios de Mantenimiento -->
# <a href="kilometraje/recordatorios/" class="reporte-card">
#   <span class="reporte-badge">🚨 Proactivo</span>
#   <div class="reporte-icon">🚨</div>
#   <h3 class="reporte-title">Recordatorios de Mantenimiento</h3>
```

---

## 🔧 Comandos Rápidos (Todo en Uno)

```bash
# Ejecutar TODO esto en el servidor:
cd /ruta/al/proyecto/e_garage
git pull origin main
git checkout HEAD -- templates/taller/reportes/reportes.html
python manage.py shell -c "from django.core.cache import cache; cache.clear()"
find . -type f -name "*.pyc" -delete
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null
sudo systemctl restart gunicorn
```

---

## 🧪 Verificación

Después de ejecutar los comandos:

1. **Acceder a:** `http://tu-servidor/reportes/`
2. **Buscar:** "Recordatorios de Mantenimiento" en la sección "Reportes Destacados"
3. **Debe aparecer:** Una card con icono 🚨 y el texto "Recordatorios de Mantenimiento"

---

## ⚠️ Si AÚN No Aparece

### Verificar Permisos del Archivo

```bash
# Verificar permisos
ls -la templates/taller/reportes/reportes.html

# Si no tiene permisos de lectura:
chmod 644 templates/taller/reportes/reportes.html
```

### Verificar que Django Encuentra el Template

```bash
python manage.py shell
# En el shell:
>>> from django.template.loader import get_template
>>> template = get_template('taller/reportes/reportes.html')
>>> # Si no hay error, Django encuentra el template
```

### Verificar Logs del Servidor

```bash
# Ver errores en tiempo real
tail -f /var/log/gunicorn/error.log

# O según tu configuración:
tail -f /var/log/apache2/error.log
tail -f /ruta/al/proyecto/logs/error.log
```

### Forzar Recarga del Template

```bash
# Si usas mod_wsgi, tocar el archivo para forzar recarga
touch templates/taller/reportes/reportes.html
sudo systemctl restart apache2
```

---

## 📋 Checklist Final

- [ ] `git pull origin main` ejecutado
- [ ] Template `reportes.html` tiene el enlace (verificado con grep)
- [ ] Cache de Django limpiado
- [ ] Cache de Python limpiado (.pyc eliminados)
- [ ] Servidor reiniciado
- [ ] Permisos del archivo correctos
- [ ] Sin errores en logs
- [ ] Template accesible desde Django shell

---

## 🆘 Último Recurso

Si NADA funciona, descargar el archivo directamente:

```bash
# Desde el servidor, descargar el archivo correcto:
curl -o templates/taller/reportes/reportes.html \
  https://raw.githubusercontent.com/mauricioatlanta/e_garage/main/templates/taller/reportes/reportes.html

# Luego reiniciar:
sudo systemctl restart gunicorn
```

---

**¡Ejecuta estos comandos y el enlace debería aparecer! 🚀**

