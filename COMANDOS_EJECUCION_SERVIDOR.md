# 🚀 Comandos de Ejecución en Servidor de Producción

**Fecha**: 2025-12-08  
**Estado**: ✅ **LISTO PARA EJECUTAR**

---

## ✅ Verificación Local Completada

- ✅ Archivos críticos presentes:
  - ✅ `staticfiles/js/ios-password-fix.js`
  - ✅ `staticfiles/manifest.json`
  - ✅ `staticfiles/sw.js`
- ✅ `collectstatic` ejecutado localmente (verificación)
- ✅ `ADMIN_AUDIT_PHONE` configurado en `settings.py` (`+56963607348`)

---

## 🔴 PASOS CRÍTICOS A EJECUTAR EN EL SERVIDOR

### Paso 1: Verificar Credenciales WhatsApp 🔴 **CRÍTICO**

**Ejecutar en el servidor de producción:**

#### Opción A: Verificar Variables de Entorno
```bash
echo $WHATSAPP_API_TOKEN
echo $WHATSAPP_BUSINESS_ID
```

**Si no están configuradas**, usar Opción B.

#### Opción B: Verificar Base de Datos
```bash
python manage.py shell
```

```python
from taller.models.notificacion import ConfiguracionNotificacion

# Verificar configuración activa
configs = ConfiguracionNotificacion.objects.filter(
    whatsapp_activo=True,
    whatsapp_api_token__isnull=False,
    whatsapp_numero_business__isnull=False
)

if configs.exists():
    print(f"✅ {configs.count()} configuración(es) activa(s)")
    for config in configs:
        print(f"  - Empresa: {config.empresa.nombre_taller}")
        print(f"  - Business ID: {config.whatsapp_numero_business}")
else:
    print("⚠️ No hay configuración activa")
    print("   Verificar variables de entorno WHATSAPP_API_TOKEN y WHATSAPP_BUSINESS_ID")
```

**✅ Verificación**: Al menos una opción debe estar configurada y activa

---

### Paso 2: Ejecutar collectstatic 🔴 **CRÍTICO**

**Ejecutar en el servidor de producción:**

```bash
python manage.py collectstatic --noinput
```

**Verificación post-ejecución:**
```bash
# Verificar que los archivos están en STATIC_ROOT
ls -la staticfiles/js/ios-password-fix.js
ls -la staticfiles/manifest.json
ls -la staticfiles/sw.js
```

**✅ Verificación**: Los 3 archivos deben existir en `staticfiles/`

---

### Paso 3: Reiniciar Aplicación 🔴 **CRÍTICO**

**Ejecutar en el servidor de producción (elegir según tu setup):**

#### Si usas systemd:
```bash
sudo systemctl restart egarage
```

#### Si usas supervisor:
```bash
sudo supervisorctl restart egarage
```

#### Si usas gunicorn directamente:
```bash
pkill -HUP gunicorn
```

**✅ Verificación**: La aplicación debe estar corriendo sin errores

```bash
# Verificar estado (ejemplo con systemd)
sudo systemctl status egarage
```

---

## 🎯 Verificaciones Post-Despliegue

### Verificación A: Auditoría y Cortesía 🔴 **CRÍTICO**

1. **Acceder a la interfaz:**
   ```
   https://tu-dominio.com/admin-monitoring/cortesia/
   ```

2. **Otorgar extensión de prueba:**
   - **Email**: `[EMAIL_DE_USUARIO_PRUEBA]`
   - **Duración**: `12 meses`
   - **Razón**: `"Prueba de despliegue - Verificación auditoría"`

3. **Verificaciones inmediatas:**
   - ✅ Cliente recibe Email de cortesía
   - ✅ Cliente recibe WhatsApp de cortesía
   - ✅ **TÚ recibes WhatsApp de auditoría en `+56963607348`** ⬅️ **PRUEBA FINAL**

**Mensaje esperado:**
```
🚨 AUDITORÍA - CORTESÍA APROBADA
✅ Extensión de plan ejecutada por Admin.
👤 USUARIO: [email]
🎁 DURACIÓN: 12 Meses
📜 RAZÓN: Prueba de despliegue - Verificación auditoría
📅 NUEVA FECHA FIN: [fecha]
```

**Si recibes el WhatsApp de auditoría**: ✅ **Fase 2 operativa al 100%**

---

### Verificación B: Fix iOS y PWA 🔴 **CRÍTICO**

**Dispositivo requerido**: iPhone (preferiblemente el modelo del suscriptor que reportó el bug)

#### 1. Prueba del Fix de Contraseña

**A. Login:**
1. Abrir formulario de login en iPhone
2. Escribir contraseña en el campo
3. Verificar:
   - ✅ Los caracteres se muestran como **puntos (•)** mientras escribes
   - ✅ **No hay espacios** entre caracteres
   - ✅ El **cursor no se mueve** incorrectamente
   - ✅ Se puede **iniciar sesión** exitosamente

**B. Registro:**
1. Abrir formulario de registro en iPhone
2. Escribir contraseña en ambos campos (password1 y password2)
3. Verificar:
   - ✅ Los caracteres se muestran correctamente
   - ✅ El formulario se **envía exitosamente**
   - ✅ **No hay errores** de validación por campo vacío

**Si el login/registro funciona correctamente**: ✅ **Bug de contraseña resuelto**

#### 2. Prueba de PWA

**A. Verificar Opción de Instalación:**
1. Abrir la web en iPhone
2. Verificar que aparece la opción "Agregar a pantalla de inicio"
   - **Safari iOS**: Menú compartir → "Agregar a pantalla de inicio"

**B. Instalar y Verificar:**
1. Instalar la PWA
2. Verificar:
   - ✅ Se abre en **pantalla completa** (sin barra de URL)
   - ✅ Los **íconos** se muestran correctamente
   - ✅ La **carga es rápida** (usa caché del Service Worker)
   - ✅ Funciona **offline** (páginas cacheadas se cargan)

**Si la PWA se instala y funciona**: ✅ **Acceso rápido implementado**

---

## ✅ Criterios de Éxito Final

### Fase 2: Cortesías/Auditoría
- [ ] WhatsApp de auditoría llega a `+56963607348`
- [ ] Cliente recibe notificaciones (Email + WhatsApp)
- [ ] Registro en LogAuditoria creado
- [ ] Fecha de expiración actualizada

### Fase 3: Fix iOS/PWA
- [ ] Campo de contraseña funciona en iPhone
- [ ] Login/registro se completa exitosamente
- [ ] PWA se instala correctamente
- [ ] PWA funciona en pantalla completa

---

## 🚨 Diagnóstico de Problemas

### WhatsApp de Auditoría No Llega

**Diagnóstico:**
1. Verificar credenciales (Paso 1)
2. Revisar logs del servidor:
   ```bash
   tail -f /ruta/a/logs/django.log | grep -i whatsapp
   ```
3. Verificar que `ADMIN_AUDIT_PHONE` está en `settings.py`:
   ```python
   # Debe ser: "+56963607348"
   ADMIN_AUDIT_PHONE = os.getenv("ADMIN_AUDIT_PHONE", "+56963607348")
   ```

### Fix iOS No Funciona

**Diagnóstico:**
1. Verificar que el script se carga:
   ```javascript
   // En Safari iOS, abrir consola y ejecutar:
   console.log(document.querySelector('script[src*="ios-password-fix"]'));
   ```
2. Verificar atributos del campo:
   ```javascript
   const input = document.querySelector('input[type="password"]');
   console.log('autocapitalize:', input.getAttribute('autocapitalize'));
   console.log('autocorrect:', input.getAttribute('autocorrect'));
   ```
3. Verificar que `collectstatic` se ejecutó (Paso 2)

### PWA No Se Instala

**Diagnóstico:**
1. Verificar HTTPS (requerido, excepto localhost)
2. Verificar Service Worker (DevTools → Application → Service Workers)
3. Verificar Manifest (DevTools → Application → Manifest)
4. Verificar que `collectstatic` se ejecutó (Paso 2)

---

## 📋 Checklist de Ejecución

### Pre-Despliegue
- [x] Código subido al servidor
- [ ] **Paso 1**: Credenciales WhatsApp verificadas
- [ ] **Paso 2**: `collectstatic` ejecutado
- [ ] **Paso 3**: Aplicación reiniciada

### Post-Despliegue
- [ ] **Verificación A**: WhatsApp de auditoría recibido
- [ ] **Verificación A**: Cliente recibió notificaciones
- [ ] **Verificación B**: Fix iOS funciona en iPhone
- [ ] **Verificación B**: PWA se instala y funciona

---

**¡Éxito con el despliegue! 🚀**



