# 📋 Instrucciones para Actualizar Cambios en el Servidor

## 🎯 Resumen de Cambios Implementados

Se ha implementado un sistema completo de kilometraje, trazabilidad de garantías, recordatorios de mantenimiento, historial digital y portal del cliente.

---

## 📁 Archivos Nuevos Creados

### Modelos
- `taller/models/kilometraje.py` - Modelo KilometrajeRegistro
- `taller/portal/models.py` - Modelos ClienteToken y ClienteCredencial

### Vistas y Lógica
- `taller/reportes/kilometraje_reportes.py` - Módulo de reportes de kilometraje
- `taller/utils/garantias.py` - Utilidades de garantías
- `taller/portal/views.py` - Vistas del portal del cliente
- `taller/portal/urls.py` - URLs del portal

### Templates
- `templates/taller/reportes/recordatorios_mantenimiento.html`
- `templates/taller/reportes/verificar_garantia.html`
- `templates/taller/reportes/historial_vehiculo.html`
- `templates/taller/reportes/historial_vehiculo_pdf.html`
- `templates/taller/portal/login.html`
- `templates/taller/portal/historial.html`
- `templates/taller/portal/historial_vehiculo.html`

### Documentación
- `IMPLEMENTACION_GARANTIAS_COMPLETA.md`
- `IMPLEMENTACION_WIDGET_DASHBOARD_COMPLETA.md`
- `IMPLEMENTACION_PORTAL_CLIENTE_COMPLETA.md`
- `IMPLEMENTACION_EXPORTACIONES_COMPLETA.md`
- `IMPLEMENTACION_PORTAL_CLIENTE_BASE.md`
- `ENLACE_HISTORIAL_AGREGADO.md`
- `RESUMEN_IMPLEMENTACION_COMPLETA_KILOMETRAJE.md`
- `ESTADO_FINAL_IMPLEMENTACION.md`

---

## 📝 Archivos Modificados

### Modelos
- `taller/models/vehiculos.py` - Agregada propiedad `kilometraje_actual` y métodos
- `taller/models/__init__.py` - Exportación de KilometrajeRegistro

### Formularios
- `taller/forms/documento_form.py` - Integración de `kilometraje_ingreso`

### Vistas
- `taller/reportes/views.py` - Vistas de recordatorios, garantías, historial, exportaciones
- `taller/documentos/views_country_aware.py` - Detección automática de garantías
- `taller/reportes/urls.py` - Rutas de kilometraje y exportaciones

### Templates
- `templates/taller/reportes/dashboard_inteligencia_operativa.html` - Widget de alertas
- `templates/taller/reportes/reportes.html` - Enlace a recordatorios
- `templates/taller/common/vehiculos/vehiculo_detail.html` - Enlaces al historial

### URLs
- `gestion_taller/urls.py` - Ruta del portal del cliente

---

## 🚀 Pasos para Actualizar en el Servidor

### 1. Hacer Commit y Push de los Cambios

```bash
# Verificar cambios
git status

# Agregar todos los archivos nuevos y modificados
git add .

# Hacer commit
git commit -m "Implementación completa: Sistema de Kilometraje, Garantías, Recordatorios, Historial Digital y Portal del Cliente"

# Push al repositorio
git push origin main
# o
git push origin master
```

### 2. En el Servidor - Actualizar Código

```bash
# Conectarse al servidor (SSH)
ssh usuario@servidor

# Navegar al directorio del proyecto
cd /ruta/al/proyecto/e_garage

# Actualizar código desde el repositorio
git pull origin main
# o
git pull origin master
```

### 3. Crear y Aplicar Migraciones

```bash
# Crear migraciones para los nuevos modelos
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Verificar que las migraciones se aplicaron correctamente
python manage.py showmigrations
```

### 4. Verificar Dependencias

```bash
# Instalar/actualizar dependencias si es necesario
pip install weasyprint openpyxl

# O si usas requirements.txt
pip install -r requirements.txt
```

### 5. Recolectar Archivos Estáticos (si aplica)

```bash
python manage.py collectstatic --noinput
```

### 6. Reiniciar Servicios

#### Si usas Gunicorn/uWSGI:
```bash
# Reiniciar Gunicorn
sudo systemctl restart gunicorn
# o
sudo supervisorctl restart gunicorn

# Reiniciar uWSGI
sudo systemctl restart uwsgi
# o
touch /ruta/al/proyecto/reload
```

#### Si usas Apache:
```bash
sudo systemctl restart apache2
# o
sudo service apache2 restart
```

#### Si usas Nginx + Gunicorn:
```bash
sudo systemctl restart gunicorn
sudo systemctl reload nginx
```

### 7. Verificar que Todo Funciona

```bash
# Verificar que el servidor responde
curl http://localhost:8000/health/

# Verificar logs por errores
tail -f /var/log/gunicorn/error.log
# o
tail -f /ruta/al/proyecto/logs/error.log
```

---

## ⚠️ Verificaciones Post-Despliegue

### 1. Verificar Migraciones Aplicadas

```bash
python manage.py showmigrations portal
python manage.py showmigrations taller
```

### 2. Verificar URLs

- `/portal/` - Debe mostrar login
- `/reportes/kilometraje/recordatorios/` - Debe mostrar recordatorios
- `/reportes/kilometraje/verificar-garantia/` - Debe mostrar verificación
- `/reportes/inteligencia/` - Debe mostrar widget de alertas

### 3. Probar Funcionalidades

1. **Crear un documento con kilometraje:**
   - Crear nuevo documento
   - Ingresar kilometraje
   - Verificar que se crea KilometrajeRegistro

2. **Ver historial de vehículo:**
   - Ir a ficha de vehículo
   - Hacer clic en "Ver Historial"
   - Verificar que muestra historial completo

3. **Exportar PDF:**
   - Desde historial, hacer clic en "Exportar PDF"
   - Verificar que se genera PDF correctamente

4. **Portal del Cliente:**
   - Acceder a `/portal/`
   - Generar token para un cliente
   - Probar acceso con token

---

## 🔧 Comandos Útiles para Troubleshooting

### Ver errores en tiempo real:
```bash
tail -f /var/log/gunicorn/error.log
```

### Verificar que Python encuentra los módulos:
```bash
python manage.py shell
>>> from taller.portal.models import ClienteToken
>>> from taller.models.kilometraje import KilometrajeRegistro
```

### Verificar configuración de Django:
```bash
python manage.py check
```

### Limpiar cache (si usas cache):
```bash
python manage.py clear_cache
# o
python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()
```

---

## 📊 Checklist de Despliegue

- [ ] Código actualizado en servidor (`git pull`)
- [ ] Migraciones creadas (`makemigrations`)
- [ ] Migraciones aplicadas (`migrate`)
- [ ] Dependencias instaladas (`weasyprint`, `openpyxl`)
- [ ] Archivos estáticos recolectados (`collectstatic`)
- [ ] Servicios reiniciados (Gunicorn/uWSGI/Apache)
- [ ] URLs verificadas (portal, reportes)
- [ ] Funcionalidades probadas (crear documento, historial, PDF)
- [ ] Logs revisados (sin errores críticos)

---

## 🆘 Si Hay Problemas

### Error: "No module named 'taller.portal'"
- Verificar que `taller/portal/__init__.py` existe
- Reiniciar servidor Python

### Error: "Table 'taller_portal_clientetoken' doesn't exist"
- Aplicar migraciones: `python manage.py migrate`

### Error: "WeasyPrint not found"
- Instalar: `pip install weasyprint`

### Error: "openpyxl not found"
- Instalar: `pip install openpyxl`

### Error 500 en portal
- Revisar logs: `tail -f /var/log/gunicorn/error.log`
- Verificar que las URLs están configuradas en `gestion_taller/urls.py`

---

## ✅ Confirmación de Despliegue Exitoso

Una vez completados todos los pasos, deberías poder:

1. ✅ Crear documentos con kilometraje
2. ✅ Ver historial de vehículos
3. ✅ Exportar historial a PDF/Excel
4. ✅ Ver recordatorios de mantenimiento
5. ✅ Verificar garantías automáticamente
6. ✅ Ver widget de alertas en dashboard
7. ✅ Acceder al portal del cliente

---

**¡Listo para actualizar en el servidor! 🚀**

