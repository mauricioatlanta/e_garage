# ✅ CHECKLIST DE DESPLIEGUE EN SERVIDOR

**Fecha**: 2025-01-27  
**Proyecto**: eGarage  
**Versión**: 1.0

---

## 📦 ARCHIVOS A SUBIR AL SERVIDOR

### **🆕 ARCHIVOS NUEVOS (3 archivos)**

#### **1. Vista de Administración**
- [ ] `taller/views_extra/admin_suscriptores.py`
  - **Ruta completa**: `taller/views_extra/admin_suscriptores.py`
  - **Tamaño aproximado**: ~220 líneas
  - **Función**: Panel de administración de suscriptores

#### **2. Templates de Admin**
- [ ] `templates/admin/suscriptores/lista_suscriptores.html`
  - **Ruta completa**: `templates/admin/suscriptores/lista_suscriptores.html`
  - **Tamaño aproximado**: ~330 líneas
  - **Función**: Lista principal de suscriptores

- [ ] `templates/admin/suscriptores/detalle_suscriptor.html`
  - **Ruta completa**: `templates/admin/suscriptores/detalle_suscriptor.html`
  - **Tamaño aproximado**: ~150 líneas
  - **Función**: Vista de detalle de suscriptor

---

### **📝 ARCHIVOS MODIFICADOS (8 archivos)**

#### **1. Correcciones de Registro**
- [ ] `taller/templates/suscripcion/registro.html`
  - **Cambios**: Sistema de mensajes, renderizado mejorado
  - **Backup**: `taller/templates/suscripcion/registro.html.backup`

- [ ] `taller/reportes/services/registration_service.py`
  - **Cambios**: Retorna info de email, sincronización de estados
  - **Backup**: `taller/reportes/services/registration_service.py.backup`

- [ ] `taller/views_extra/suscripcion.py`
  - **Cambios**: Logging mejorado, notificaciones de email
  - **Backup**: `taller/views_extra/suscripcion.py.backup`

- [ ] `taller/backends/egarage_email.py`
  - **Cambios**: Excepción personalizada, lanza errores
  - **Backup**: `taller/backends/egarage_email.py.backup`

- [ ] `taller/forms/suscripcion.py`
  - **Cambios**: Eliminada creación duplicada de suscripción
  - **Backup**: `taller/forms/suscripcion.py.backup`

#### **2. Panel de Administración**
- [ ] `gestion_taller/urls.py`
  - **Cambios**: 3 nuevas rutas agregadas
  - **Backup**: `gestion_taller/urls.py.backup`

#### **3. Notificaciones**
- [ ] `taller/utils/notificaciones_suscripcion.py`
  - **Cambios**: Mensajes más cálidos, incluyen meses
  - **Backup**: `taller/utils/notificaciones_suscripcion.py.backup`

- [ ] `templates/email/renovacion_exitosa.html`
  - **Cambios**: Mensaje más cálido, cierre mejorado
  - **Backup**: `templates/email/renovacion_exitosa.html.backup`

---

## 🔄 PROCESO DE DESPLIEGUE

### **PASO 1: Preparación** ⏱️ 5 minutos

- [ ] Conectarse al servidor (SSH/FTP)
- [ ] Navegar al directorio del proyecto
- [ ] Verificar espacio en disco disponible
- [ ] Verificar permisos de escritura

### **PASO 2: Backup** ⏱️ 3 minutos

```bash
# Crear directorio de backup
mkdir -p backups/$(date +%Y%m%d_%H%M%S)

# Backup de archivos modificados
cp taller/templates/suscripcion/registro.html backups/*/registro.html.backup
cp taller/reportes/services/registration_service.py backups/*/registration_service.py.backup
cp taller/views_extra/suscripcion.py backups/*/suscripcion.py.backup
cp taller/backends/egarage_email.py backups/*/egarage_email.py.backup
cp taller/forms/suscripcion.py backups/*/suscripcion.py.backup
cp gestion_taller/urls.py backups/*/urls.py.backup
cp taller/utils/notificaciones_suscripcion.py backups/*/notificaciones_suscripcion.py.backup
cp templates/email/renovacion_exitosa.html backups/*/renovacion_exitosa.html.backup
```

- [ ] Backup completado
- [ ] Verificar que los backups existen

### **PASO 3: Subir Archivos Nuevos** ⏱️ 5 minutos

- [ ] Crear directorio si no existe: `templates/admin/suscriptores/`
- [ ] Subir `taller/views_extra/admin_suscriptores.py`
- [ ] Subir `templates/admin/suscriptores/lista_suscriptores.html`
- [ ] Subir `templates/admin/suscriptores/detalle_suscriptor.html`
- [ ] Verificar permisos (644 para archivos, 755 para directorios)

### **PASO 4: Actualizar Archivos Modificados** ⏱️ 5 minutos

- [ ] Actualizar `taller/templates/suscripcion/registro.html`
- [ ] Actualizar `taller/reportes/services/registration_service.py`
- [ ] Actualizar `taller/views_extra/suscripcion.py`
- [ ] Actualizar `taller/backends/egarage_email.py`
- [ ] Actualizar `taller/forms/suscripcion.py`
- [ ] Actualizar `gestion_taller/urls.py`
- [ ] Actualizar `taller/utils/notificaciones_suscripcion.py`
- [ ] Actualizar `templates/email/renovacion_exitosa.html`

### **PASO 5: Verificación** ⏱️ 5 minutos

```bash
# Verificar sintaxis Python
python manage.py check

# Verificar imports
python manage.py shell << EOF
from taller.views_extra.admin_suscriptores import admin_suscriptores
from taller.backends.egarage_email import EmailBackendError
exit()
EOF

# Verificar URLs
python manage.py show_urls | grep suscriptores
```

- [ ] Sintaxis correcta
- [ ] Imports funcionan
- [ ] URLs registradas

### **PASO 6: Reinicio (si es necesario)** ⏱️ 2 minutos

```bash
# Reiniciar servidor web (ejemplo con systemd)
sudo systemctl restart gunicorn
# o
sudo systemctl restart uwsgi
# o
sudo service apache2 restart
```

- [ ] Servidor reiniciado
- [ ] Verificar que el servicio está activo

---

## 🧪 PRUEBAS POST-DESPLIEGUE

### **PRUEBA 1: Registro de Usuario** ⏱️ 5 minutos

- [ ] Ir a `/registro/`
- [ ] Llenar formulario de registro
- [ ] **Verificar**: Se muestran mensajes de éxito/error
- [ ] **Verificar**: Redirección al dashboard después de registro
- [ ] **Verificar**: Llega correo de bienvenida
- [ ] **Verificar**: Usuario puede iniciar sesión

### **PRUEBA 2: Panel de Administración** ⏱️ 10 minutos

- [ ] Acceder como staff a `/admin/suscriptores/`
- [ ] **Verificar**: Se carga la lista de suscriptores
- [ ] **Verificar**: Filtros funcionan (país, status, días)
- [ ] **Verificar**: Búsqueda funciona
- [ ] **Verificar**: Paginación funciona
- [ ] Probar extensión de suscripción (1 mes)
- [ ] **Verificar**: Llega email de notificación
- [ ] **Verificar**: Llega WhatsApp de notificación
- [ ] **Verificar**: Se actualiza fecha de vencimiento
- [ ] **Verificar**: Se registra en auditoría

### **PRUEBA 3: Logs** ⏱️ 3 minutos

```bash
# Revisar logs para errores
tail -50 logs/django.log | grep -i "error\|exception"

# Revisar logs de registro
tail -50 logs/django.log | grep -i "registro\|suscripcion"

# Revisar logs de notificaciones
tail -50 logs/django.log | grep -i "email\|whatsapp"
```

- [ ] No hay errores críticos
- [ ] Registros se están guardando
- [ ] Notificaciones se están enviando

---

## ⚠️ ROLLBACK (Si algo falla)

### **Restaurar desde Backup**

```bash
# Restaurar archivos modificados
cp backups/*/registro.html.backup taller/templates/suscripcion/registro.html
cp backups/*/registration_service.py.backup taller/reportes/services/registration_service.py
cp backups/*/suscripcion.py.backup taller/views_extra/suscripcion.py
cp backups/*/egarage_email.py.backup taller/backends/egarage_email.py
cp backups/*/suscripcion.py.backup taller/forms/suscripcion.py
cp backups/*/urls.py.backup gestion_taller/urls.py
cp backups/*/notificaciones_suscripcion.py.backup taller/utils/notificaciones_suscripcion.py
cp backups/*/renovacion_exitosa.html.backup templates/email/renovacion_exitosa.html

# Eliminar archivos nuevos (opcional)
rm taller/views_extra/admin_suscriptores.py
rm -rf templates/admin/suscriptores/

# Reiniciar servidor
sudo systemctl restart gunicorn
```

---

## 📊 RESUMEN

- **Archivos nuevos**: 3
- **Archivos modificados**: 8
- **Total de archivos**: 11
- **Tiempo estimado**: 25-30 minutos
- **Riesgo**: Bajo (backward compatible)
- **Rollback**: Disponible (backups creados)

---

## ✅ CHECKLIST FINAL

- [ ] Todos los archivos subidos
- [ ] Backups creados
- [ ] Verificación completada
- [ ] Pruebas realizadas
- [ ] Logs revisados
- [ ] Sin errores críticos
- [ ] Funcionalidades operativas

---

## 📞 CONTACTO DE SOPORTE

Si encuentras problemas:

1. Revisar logs: `logs/django.log`
2. Verificar configuración de email
3. Verificar que usuario es staff para panel admin
4. Revisar permisos de archivos

---

**Última actualización**: 2025-01-27  
**Estado**: ✅ Listo para despliegue

