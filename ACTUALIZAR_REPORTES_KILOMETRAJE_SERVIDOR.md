# 🔧 Actualizar Reportes de Kilometraje en el Servidor

## ⚠️ Problema

Los cambios de los reportes de kilometraje no se están viendo en el servidor.

---

## ✅ Solución: Pasos Específicos

### 1. Verificar que el Código se Actualizó

```bash
# En el servidor
cd /ruta/al/proyecto/e_garage

# Verificar que tienes el último commit
git log --oneline -1
# Debe mostrar: "Implementación completa: Sistema de Kilometraje..."

# Si no está actualizado, hacer pull
git pull origin main
```

### 2. Verificar que los Archivos Existen

```bash
# Verificar que existe el módulo de reportes
ls -la taller/reportes/kilometraje_reportes.py

# Verificar que existe el modelo
ls -la taller/models/kilometraje.py

# Verificar que existen las vistas
grep -n "recordatorios_mantenimiento\|verificar_garantia\|historial_mantenimiento" taller/reportes/views.py
```

### 3. Aplicar Migraciones (CRÍTICO)

```bash
# Crear migraciones para KilometrajeRegistro
python manage.py makemigrations taller

# Aplicar migraciones
python manage.py migrate

# Verificar que la tabla existe
python manage.py dbshell
# Luego en SQL:
# .tables (SQLite) o \dt (PostgreSQL) o SHOW TABLES; (MySQL)
# Debe aparecer: taller_kilometrajeregistro
```

### 4. Reiniciar el Servidor Python (MUY IMPORTANTE)

El servidor Python debe reiniciarse para cargar los nuevos módulos:

```bash
# Opción A: Gunicorn
sudo systemctl restart gunicorn
# o
sudo supervisorctl restart gunicorn

# Opción B: uWSGI
sudo systemctl restart uwsgi
# o
touch /ruta/al/proyecto/reload

# Opción C: Apache + mod_wsgi
sudo systemctl restart apache2

# Opción D: Si usas runserver (desarrollo)
# Ctrl+C y luego:
python manage.py runserver
```

### 5. Limpiar Cache de Python (si aplica)

```bash
# Eliminar archivos .pyc
find . -type f -name "*.pyc" -delete
find . -type d -name "__pycache__" -exec rm -r {} +

# O más específico:
find taller/reportes -type f -name "*.pyc" -delete
find taller/models -type f -name "*.pyc" -delete
```

### 6. Verificar que las URLs Están Configuradas

```bash
# Verificar que las URLs de reportes incluyen kilometraje
grep -n "kilometraje" taller/reportes/urls.py

# Debe mostrar:
# - kilometraje/recordatorios/
# - kilometraje/historial/
# - kilometraje/verificar-garantia/
```

### 7. Verificar que el Módulo se Importa Correctamente

```bash
# Probar importación en shell de Django
python manage.py shell

# En el shell:
>>> from taller.reportes.kilometraje_reportes import ReporteKilometraje
>>> from taller.models.kilometraje import KilometrajeRegistro
>>> # Si no hay error, los módulos están bien
```

---

## 🧪 Pruebas Específicas

### 1. Probar URL de Recordatorios

```bash
# Desde el navegador o curl:
curl http://tu-servidor/reportes/kilometraje/recordatorios/

# O acceder desde el navegador:
http://tu-servidor/reportes/kilometraje/recordatorios/
```

### 2. Probar URL de Verificación de Garantía

```bash
curl http://tu-servidor/reportes/kilometraje/verificar-garantia/
```

### 3. Verificar Widget en Dashboard

```bash
# Acceder al dashboard
http://tu-servidor/reportes/inteligencia/

# Debe mostrar el widget de "Alertas de Negocio"
```

---

## 🔍 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'taller.reportes.kilometraje_reportes'"

**Solución:**
```bash
# Verificar que el archivo existe
ls -la taller/reportes/kilometraje_reportes.py

# Si existe, reiniciar servidor
sudo systemctl restart gunicorn
```

### Error: "Table 'taller_kilometrajeregistro' doesn't exist"

**Solución:**
```bash
# Aplicar migraciones
python manage.py makemigrations
python manage.py migrate
```

### Error: "NameError: name 'ReporteKilometraje' is not defined"

**Solución:**
```bash
# Verificar que el import está en views.py
grep "from taller.reportes.kilometraje_reportes import" taller/reportes/views.py

# Si no está, el archivo no se actualizó correctamente
git pull origin main
```

### Las URLs no funcionan (404)

**Solución:**
```bash
# Verificar que las URLs están en urls.py
grep "kilometraje" taller/reportes/urls.py

# Verificar que el archivo urls.py principal incluye reportes
grep "reportes" gestion_taller/urls.py

# Reiniciar servidor
sudo systemctl restart gunicorn
```

---

## 📋 Checklist Completo

- [ ] Código actualizado (`git pull origin main`)
- [ ] Archivo `kilometraje_reportes.py` existe
- [ ] Archivo `kilometraje.py` (modelo) existe
- [ ] Migraciones aplicadas (`migrate`)
- [ ] Tabla `taller_kilometrajeregistro` existe en BD
- [ ] Servidor reiniciado
- [ ] Cache de Python limpiado
- [ ] URLs verificadas
- [ ] Módulos se importan correctamente
- [ ] URLs funcionan (no 404)

---

## 🚀 Comandos Rápidos (Todo en Uno)

```bash
# En el servidor, ejecutar todo esto:
cd /ruta/al/proyecto/e_garage
git pull origin main
python manage.py makemigrations
python manage.py migrate
find . -type f -name "*.pyc" -delete
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null
sudo systemctl restart gunicorn
# o según tu configuración:
# sudo systemctl restart uwsgi
# sudo systemctl restart apache2
```

---

## ✅ Verificación Final

Después de ejecutar todos los pasos, verifica:

1. **Dashboard:** `/reportes/inteligencia/` - Debe mostrar widget de alertas
2. **Recordatorios:** `/reportes/kilometraje/recordatorios/` - Debe mostrar lista
3. **Garantías:** `/reportes/kilometraje/verificar-garantia/` - Debe mostrar formulario
4. **Historial:** Desde ficha de vehículo, clic en "Ver Historial" - Debe funcionar

---

**¡Si después de estos pasos aún no funciona, revisa los logs del servidor!**

