# 🚀 Siguiente Paso: Actualizar en el Servidor

## ✅ Cambios Subidos al Repositorio

Los cambios han sido commiteados y pusheados exitosamente al repositorio.

---

## 📋 Pasos en el Servidor

### 1. Conectarse al Servidor

```bash
ssh usuario@servidor
# o
ssh -i /ruta/a/llave.pem usuario@servidor
```

### 2. Ir al Directorio del Proyecto

```bash
cd /ruta/al/proyecto/e_garage
# Ejemplo común:
# cd /var/www/egarage
# o
# cd /home/usuario/egarage
```

### 3. Actualizar Código desde Git

```bash
# Verificar rama actual
git branch

# Actualizar código
git pull origin main
# o si tu rama es master:
# git pull origin master
```

### 4. Crear Migraciones

```bash
# Crear migraciones para los nuevos modelos
python manage.py makemigrations

# Esto debería crear:
# - taller/migrations/XXXX_kilometrajeregistro.py
# - taller/portal/migrations/0001_initial.py (si no existe)
```

### 5. Aplicar Migraciones

```bash
# Aplicar todas las migraciones pendientes
python manage.py migrate

# Verificar que se aplicaron correctamente
python manage.py showmigrations portal
python manage.py showmigrations taller
```

### 6. Instalar Dependencias (si es necesario)

```bash
# Instalar librerías para PDF y Excel
pip install weasyprint openpyxl

# O si usas un entorno virtual:
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows
pip install weasyprint openpyxl
```

### 7. Recolectar Archivos Estáticos

```bash
python manage.py collectstatic --noinput
```

### 8. Reiniciar el Servidor

#### Opción A: Gunicorn
```bash
sudo systemctl restart gunicorn
# o
sudo supervisorctl restart gunicorn
```

#### Opción B: uWSGI
```bash
sudo systemctl restart uwsgi
# o si usas archivo de configuración:
touch /ruta/al/proyecto/reload
```

#### Opción C: Apache
```bash
sudo systemctl restart apache2
# o
sudo service apache2 restart
```

#### Opción D: Desarrollo (runserver)
```bash
# Si estás en desarrollo, simplemente reinicia el servidor
# Ctrl+C y luego:
python manage.py runserver
```

### 9. Verificar que Todo Funciona

```bash
# Verificar salud del servidor
curl http://localhost:8000/health/

# Ver logs en tiempo real (si hay errores)
tail -f /var/log/gunicorn/error.log
# o
tail -f /ruta/al/proyecto/logs/error.log
```

---

## 🧪 Pruebas Post-Despliegue

### 1. Verificar URLs

- ✅ `/portal/` - Debe mostrar login del portal
- ✅ `/reportes/kilometraje/recordatorios/` - Debe mostrar recordatorios
- ✅ `/reportes/kilometraje/verificar-garantia/` - Debe mostrar verificación
- ✅ `/reportes/inteligencia/` - Debe mostrar widget de alertas

### 2. Probar Funcionalidades

1. **Crear documento con kilometraje:**
   - Ir a crear documento
   - Seleccionar vehículo
   - Ingresar kilometraje
   - Guardar
   - Verificar que se crea el registro

2. **Ver historial:**
   - Ir a ficha de vehículo
   - Clic en "Ver Historial de Mantenimiento"
   - Verificar que muestra el historial

3. **Exportar PDF:**
   - Desde historial, clic en "Exportar PDF"
   - Verificar que se descarga el PDF

4. **Portal del cliente:**
   - Acceder a `/portal/`
   - Verificar que muestra el login

---

## ⚠️ Si Hay Problemas

### Error: "No module named 'taller.portal'"
```bash
# Verificar que el directorio existe
ls -la taller/portal/

# Reiniciar servidor Python
sudo systemctl restart gunicorn
```

### Error: "Table doesn't exist"
```bash
# Aplicar migraciones
python manage.py migrate
```

### Error: "WeasyPrint not found"
```bash
# Instalar
pip install weasyprint
```

### Error: "openpyxl not found"
```bash
# Instalar
pip install openpyxl
```

### Error 500 en alguna página
```bash
# Ver logs detallados
tail -f /var/log/gunicorn/error.log

# O en desarrollo:
python manage.py runserver --verbosity 2
```

---

## ✅ Checklist de Despliegue

- [ ] Código actualizado (`git pull`)
- [ ] Migraciones creadas (`makemigrations`)
- [ ] Migraciones aplicadas (`migrate`)
- [ ] Dependencias instaladas (`weasyprint`, `openpyxl`)
- [ ] Archivos estáticos recolectados (`collectstatic`)
- [ ] Servidor reiniciado
- [ ] URLs verificadas
- [ ] Funcionalidades probadas
- [ ] Sin errores en logs

---

## 🎯 Comandos Rápidos (Todo en Uno)

```bash
# En el servidor, ejecutar:
cd /ruta/al/proyecto/e_garage
git pull origin main
python manage.py makemigrations
python manage.py migrate
pip install weasyprint openpyxl
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
```

---

**¡Listo para ejecutar en el servidor! 🚀**

