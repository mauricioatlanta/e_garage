# Lista de Archivos para Actualizar en el Servidor
## Integración de Soporte WhatsApp y Email Centralizado

**Fecha**: 2025-01-XX  
**Descripción**: Integración centralizada de soporte (WhatsApp + Email) en toda la aplicación

---

## 📋 ARCHIVOS NUEVOS (CREAR EN SERVIDOR)

### 1. Context Processor - Soporte
```
taller/context_processors/support_context.py
```
**Descripción**: Context processor que expone variables de soporte a todos los templates

### 2. Helper de Email Centralizado
```
taller/utils/email_helper.py
```
**Descripción**: Helper centralizado para envío de emails con reply_to configurado automáticamente

---

## 🔧 ARCHIVOS MODIFICADOS (ACTUALIZAR EN SERVIDOR)

### Settings y Configuración

#### 3. Settings Principal
```
gestion_taller/settings.py
```
**Cambios**:
- ✅ Agregadas variables `SUPPORT_EMAIL`, `SUPPORT_WHATSAPP_E164`, `SUPPORT_WHATSAPP_DISPLAY`, `SUPPORT_WHATSAPP_WA_ME`
- ✅ `DEFAULT_FROM_EMAIL` y `EMAIL_HOST_USER` usan `SUPPORT_EMAIL`
- ✅ `EMAIL_HOST_PASSWORD` ahora usa `os.getenv("EMAIL_HOST_PASSWORD")` (eliminado hardcode)
- ✅ Agregado `support_context` a `TEMPLATES[0]["OPTIONS"]["context_processors"]`
- ⚠️ **IMPORTANTE**: Configurar `EMAIL_HOST_PASSWORD` en variables de entorno del servidor

#### 4. Context Processors Init
```
taller/context_processors/__init__.py
```
**Cambios**:
- ✅ Agregado import de `support_context`
- ✅ Agregado `support_context` a `__all__`

---

### Templates (Frontend)

#### 5. Template Base Global
```
templates/base.html
```
**Cambios**:
- ✅ Footer actualizado con `{{ support_email }}` y `{{ support_whatsapp_display }}`
- ✅ Link WhatsApp con `wa.me/{{ support_whatsapp_wa_me }}`

#### 6. Bienvenida Chile
```
templates/cl/es/onboarding/bienvenida.html
```
**Cambios**:
- ✅ Footer actualizado con variables de soporte centralizadas
- ✅ Eliminado hardcode de contacto

#### 7. Bienvenida USA
```
templates/us/en/onboarding/bienvenida.html
```
**Cambios**:
- ✅ Footer actualizado con variables de soporte centralizadas
- ✅ Eliminado hardcode de contacto

---

### Templates de Email

#### 8. Email: Trial Expirado
```
templates/emails/trial_expired.html
```
**Cambios**:
- ✅ Footer simplificado con `{{ support_email }}` y WhatsApp
- ✅ Eliminado texto viejo (+1-800, +57, etc.)
- ✅ HTML bien formado, sin divs duplicados

#### 9. Email: Advertencia de Expiración
```
templates/emails/subscription_expiration_warning.html
```
**Cambios**:
- ✅ Footer simplificado con `{{ support_email }}` y WhatsApp
- ✅ Eliminado texto viejo (+1-800, +57, etc.)
- ✅ HTML bien formado, sin divs duplicados

---

### PDFs y Documentos

#### 10. Template PDF
```
templates/taller/pdf/documento.html
```
**Cambios**:
- ✅ Footer actualizado con información de soporte
- ✅ Agregado: `Soporte: {{ support_email }} | WhatsApp: {{ support_whatsapp_display }}`

#### 11. Servicio de Generación de PDF
```
taller/services/document_output_service.py
```
**Cambios**:
- ✅ Contexto actualizado para incluir `support_email`, `support_whatsapp_display`, `support_whatsapp_wa_me`

---

### Comandos de Gestión

#### 12. Comando de Notificaciones de Vencimiento
```
taller/management/commands/notificar_vencimientos.py
```
**Cambios** (archivo completamente reescrito):
- ✅ Lógica corregida: notificaciones a 7, 3, 1 día y vencidas
- ✅ Anti-duplicado implementado con flags booleanos
- ✅ Agregado modo `--dry-run` para pruebas
- ✅ Optimización: `select_related("user")` para evitar N+1 queries
- ✅ Usa `send_email_with_reply_to()` del helper centralizado
- ✅ Variables de soporte centralizadas
- ✅ Documentación completa en docstring

---

### Modelos

#### 13. Modelo Empresa
```
taller/models/empresa.py
```
**Cambios**:
- ✅ Documentación mejorada en campos de notificación
- ✅ Help text agregado para `notificacion_5_dias`, `notificacion_1_dia`, `notificacion_vencido`
- ✅ Comentarios explicando reutilización de `notificacion_5_dias` para 7 y 3 días

---

## ⚠️ CONFIGURACIÓN REQUERIDA EN SERVIDOR

### Variables de Entorno

Agregar en `.env` o variables de entorno del servidor:

```bash
EMAIL_HOST_PASSWORD=tu_contraseña_aqui
```

**IMPORTANTE**: Si la contraseña estuvo expuesta en código anteriormente, **ROTARLA** inmediatamente.

---

## 📝 CHECKLIST DE DESPLIEGUE

### Antes de Desplegar

- [ ] Configurar `EMAIL_HOST_PASSWORD` en variables de entorno del servidor
- [ ] Rotar contraseña de email si estaba expuesta
- [ ] Verificar que `support@egarage.cl` esté configurado correctamente en el servidor de correo

### Durante el Despliegue

- [ ] Subir archivos nuevos (`support_context.py`, `email_helper.py`)
- [ ] Actualizar archivos modificados (lista completa arriba)
- [ ] Verificar que no haya errores de sintaxis
- [ ] Ejecutar `python manage.py collectstatic` si es necesario (para templates)
- [ ] Reiniciar aplicación/servidor web

### Después del Despliegue

- [ ] Verificar footer en home/dashboard (debe mostrar soporte)
- [ ] Verificar links de WhatsApp en templates
- [ ] Enviar email de prueba (verificar From y Reply-To)
- [ ] Generar PDF de prueba (verificar footer con soporte)
- [ ] Ejecutar `python manage.py notificar_vencimientos --dry-run` (modo prueba)
- [ ] Verificar que no haya errores en logs

---

## 🧪 COMANDOS DE PRUEBA

```bash
# Verificar context processor
python manage.py shell
>>> from taller.context_processors.support_context import support_context
>>> print(support_context(None))

# Probar comando de notificaciones (dry-run)
python manage.py notificar_vencimientos --dry-run

# Verificar settings
python manage.py shell
>>> from django.conf import settings
>>> print(settings.SUPPORT_EMAIL)
>>> print(settings.SUPPORT_WHATSAPP_DISPLAY)
```

---

## 📊 RESUMEN

- **Archivos nuevos**: 2
- **Archivos modificados**: 11
- **Total archivos a actualizar**: 13

---

## 🔗 REFERENCIAS

- Variables de soporte definidas en: `gestion_taller/settings.py` (líneas 284-289)
- Context processor registrado en: `gestion_taller/settings.py` (línea 224)
- Helper de email: `taller/utils/email_helper.py`

---

**Nota**: Todos los cambios son retrocompatibles. Si algún archivo no existe en el servidor, crearlo con el contenido correspondiente.
