# 📧 FLUJO DE REGISTRO Y PAGO - DOCUMENTACIÓN COMPLETA

**Fecha**: 26 de octubre de 2025  
**Estado**: Desarrollo → Producción

---

## 🔴 **CÓMO FUNCIONA ACTUALMENTE (DESARROLLO)**

### **Configuración Actual:**
```python
# gestion_taller/settings.py
ACCOUNT_EMAIL_VERIFICATION = 'none'  # ⚠️ SIN verificación de email
ACCOUNT_EMAIL_REQUIRED = False       # ⚠️ Email no obligatorio
```

### **Flujo ACTUAL:**

#### **Escenario 1: Plan TRIAL (Gratis)** 🎁

```
1. Usuario visita: http://127.0.0.1:8000/cl/
   ↓
2. Clic "Registrarse" → /accounts/signup/?from=cl
   ↓
3. Llena formulario:
   - Nombre, Apellido, Email, Empresa, Teléfono
   - País: Chile
   - Plan: Trial (30 días gratis)
   - Contraseña
   ↓
4. Clic "CREAR CUENTA"
   ↓
5. Sistema ejecuta (signup_complete.py):
   ├─ Crea usuario (User)
   ├─ Crea empresa (Empresa) con suscripcion_activa=True
   ├─ LOGIN AUTOMÁTICO (sin confirmar email)
   ├─ Mensaje: "¡Bienvenido! Tu prueba gratuita ha comenzado"
   └─ Redirige a: /cl/es/dashboard/
   ↓
6. Usuario entra DIRECTO al dashboard
   - ✅ Acceso INMEDIATO
   - ❌ NO recibe email de confirmación
   - ✅ Suscripción activa por 30 días
```

#### **Escenario 2: Plan PAGADO (Mensual/Semestral/Anual)** 💰

##### **Chile (Transferencia Bancaria):**

```
1. Usuario visita: http://127.0.0.1:8000/cl/
   ↓
2. Llena formulario, selecciona "Plan Mensual" ($10.000)
   ↓
3. Clic "CREAR CUENTA"
   ↓
4. Sistema ejecuta:
   ├─ Crea usuario
   ├─ Crea empresa con suscripcion_activa=FALSE
   ├─ LOGIN AUTOMÁTICO
   ├─ Mensaje: "Completa el pago para activar"
   └─ Redirige a: /cl/es/suscripcion/pago/?plan=mensual&amount=10000
   ↓
5. Usuario ve página de pago con:
   - Datos bancarios de BancoEstado
   - Formulario para subir comprobante
   ↓
6. Usuario hace transferencia desde su banco
   ↓
7. Usuario sube screenshot del comprobante
   ↓
8. Sistema crea PagoPendiente:
   ├─ estado: 'pendiente'
   ├─ comprobante: [archivo_subido]
   └─ Mensaje: "Comprobante recibido, verificación en 24-48h"
   ↓
9. ADMIN recibe notificación (o revisa manualmente /admin/)
   ↓
10. ADMIN verifica el pago:
    ├─ Ve el comprobante
    ├─ Verifica en BancoEstado
    └─ Clic "Aprobar" o "Rechazar"
    ↓
11. Si APROBADO:
    ├─ Sistema ejecuta aprobar_pago()
    ├─ empresa.suscripcion_activa = True
    ├─ empresa.fecha_fin = +30 días
    ├─ PagoPendiente.estado = 'procesado'
    └─ ❌ NO se envía email al usuario (todavía)
    ↓
12. Usuario hace login y ahora SÍ tiene acceso
```

##### **USA (PayPal):**

```
1. Usuario visita: http://127.0.0.1:8000/us/
   ↓
2. Llena formulario, selecciona "Monthly Plan" ($20)
   ↓
3. Clic "CREATE ACCOUNT"
   ↓
4. Sistema redirige a: /us/en/subscription/payment/
   ↓
5. Usuario ve botón de PayPal
   ↓
6. Clic "Pay with PayPal"
   ↓
7. PayPal procesa el pago (popup o redirect)
   ↓
8. Si ÉXITO:
   ├─ PayPal redirige a: /us/en/payment/success/
   ├─ Sistema activa suscripción automáticamente
   ├─ empresa.suscripcion_activa = True
   └─ Mensaje: "¡Pago exitoso! Tu suscripción está activa"
   ↓
9. Usuario accede al dashboard
```

---

## 🟢 **CÓMO DEBERÍA FUNCIONAR (PRODUCCIÓN)**

### **Configuración RECOMENDADA:**
```python
# gestion_taller/settings.py
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'  # ✅ Verificación OBLIGATORIA
ACCOUNT_EMAIL_REQUIRED = True              # ✅ Email REQUERIDO
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 2 # ✅ Link expira en 2 días
```

### **Flujo IDEAL:**

#### **Escenario 1: Plan TRIAL (Gratis)** 🎁

```
1. Usuario visita: https://www.egarage.cl/cl/
   ↓
2. Clic "Registrarse" → /accounts/signup/?from=cl
   ↓
3. Llena formulario + Plan: Trial
   ↓
4. Clic "CREAR CUENTA"
   ↓
5. Sistema ejecuta:
   ├─ Crea usuario (is_active=False)
   ├─ Crea empresa (suscripcion_activa=False)
   ├─ NO hace login automático
   └─ Redirige a: /accounts/confirm-email/
   ↓
6. Página de confirmación:
   "📧 Revisa tu email para confirmar tu cuenta"
   ↓
7. Sistema envía EMAIL:
   ┌────────────────────────────────────────┐
   │ 🚀 Bienvenido a eGarage                │
   │                                        │
   │ Hola Juan,                             │
   │                                        │
   │ Gracias por registrarte en eGarage.   │
   │                                        │
   │ Para activar tu cuenta y comenzar tu  │
   │ prueba gratuita de 30 días, haz clic: │
   │                                        │
   │ [CONFIRMAR CUENTA] ← Link único       │
   │                                        │
   │ Este link expira en 48 horas.         │
   │                                        │
   │ Saludos,                               │
   │ Equipo eGarage                         │
   └────────────────────────────────────────┘
   ↓
8. Usuario abre email y hace clic en link
   ↓
9. Sistema verifica el token:
   ├─ user.is_active = True
   ├─ empresa.suscripcion_activa = True
   ├─ empresa.fecha_inicio = now()
   ├─ empresa.fecha_fin = now() + 30 días
   └─ Redirige a: /accounts/login/
   ↓
10. Mensaje: "✅ Email confirmado. Inicia sesión"
    ↓
11. Usuario inicia sesión → Dashboard
    ↓
12. ¡Comienza a usar eGarage! 🎉
```

#### **Escenario 2: Plan PAGADO** 💰

##### **Chile (Transferencia):**

```
1. Usuario se registra con Plan Mensual ($10.000)
   ↓
2. Sistema:
   ├─ Crea usuario (is_active=False)
   ├─ Crea empresa (suscripcion_activa=False)
   ├─ Crea PagoPendiente (estado='pendiente')
   └─ Redirige a: /accounts/confirm-email/
   ↓
3. Usuario recibe EMAIL 1:
   ┌────────────────────────────────────────┐
   │ 📧 Confirma tu email                   │
   │                                        │
   │ Haz clic para confirmar:               │
   │ [CONFIRMAR CUENTA]                     │
   └────────────────────────────────────────┘
   ↓
4. Usuario hace clic en link
   ↓
5. Sistema:
   ├─ user.is_active = True
   ├─ empresa sigue con suscripcion_activa=False
   └─ Redirige a: /cl/es/suscripcion/pago/
   ↓
6. Usuario ve página de pago:
   - Datos bancarios
   - Formulario para subir comprobante
   ↓
7. Usuario hace transferencia y sube comprobante
   ↓
8. Sistema actualiza PagoPendiente:
   ├─ comprobante = [archivo]
   └─ Mensaje: "Comprobante recibido, revisión en 24-48h"
   ↓
9. Usuario recibe EMAIL 2:
   ┌────────────────────────────────────────┐
   │ 💰 Comprobante Recibido                │
   │                                        │
   │ Hola Juan,                             │
   │                                        │
   │ Recibimos tu comprobante de pago por   │
   │ el Plan Mensual ($10.000 CLP).        │
   │                                        │
   │ Lo verificaremos en 24-48 horas y te   │
   │ notificaremos cuando tu suscripción    │
   │ esté activa.                           │
   │                                        │
   │ Gracias por elegir eGarage.            │
   └────────────────────────────────────────┘
   ↓
10. ADMIN recibe notificación:
    ┌────────────────────────────────────────┐
    │ 🔔 Nuevo Pago Pendiente                │
    │                                        │
    │ Empresa: Taller Don Carlos             │
    │ Plan: Mensual                          │
    │ Monto: $10.000 CLP                     │
    │                                        │
    │ [VER COMPROBANTE] [APROBAR] [RECHAZAR]│
    └────────────────────────────────────────┘
    ↓
11. ADMIN revisa y APRUEBA el pago
    ↓
12. Sistema:
    ├─ empresa.suscripcion_activa = True
    ├─ empresa.fecha_fin = +30 días
    ├─ PagoPendiente.estado = 'procesado'
    └─ Envía EMAIL 3 al usuario
    ↓
13. Usuario recibe EMAIL 3:
    ┌────────────────────────────────────────┐
    │ ✅ ¡Pago Confirmado!                   │
    │                                        │
    │ Hola Juan,                             │
    │                                        │
    │ ¡Excelente noticia! Tu pago ha sido    │
    │ confirmado y tu suscripción está       │
    │ ACTIVA.                                │
    │                                        │
    │ Plan: Mensual                          │
    │ Válido hasta: 26/Nov/2025              │
    │                                        │
    │ [COMENZAR A USAR EGARAGE]              │
    │                                        │
    │ Saludos,                               │
    │ Equipo eGarage                         │
    └────────────────────────────────────────┘
    ↓
14. Usuario hace login → Dashboard activo ✅
```

##### **USA (PayPal):**

```
1. Usuario se registra con Monthly Plan ($20)
   ↓
2. Sistema:
   ├─ Crea usuario (is_active=False)
   ├─ Crea empresa (suscripcion_activa=False)
   └─ Envía EMAIL de confirmación
   ↓
3. Usuario confirma email
   ↓
4. Redirige a: /us/en/subscription/payment/
   ↓
5. Usuario paga con PayPal
   ↓
6. PayPal notifica ÉXITO (webhook o redirect)
   ↓
7. Sistema:
   ├─ Verifica pago con PayPal API
   ├─ empresa.suscripcion_activa = True
   ├─ Crea PagoPendiente (estado='procesado')
   └─ Envía EMAIL de confirmación
   ↓
8. Usuario recibe EMAIL:
   ┌────────────────────────────────────────┐
   │ ✅ Payment Confirmed!                  │
   │                                        │
   │ Hi John,                               │
   │                                        │
   │ Your payment was successful!           │
   │                                        │
   │ Plan: Monthly ($20/month)              │
   │ Next billing: Nov 26, 2025             │
   │                                        │
   │ [START USING EGARAGE]                  │
   └────────────────────────────────────────┘
   ↓
9. Usuario accede al dashboard ✅
```

---

## 📧 **TIPOS DE EMAILS**

### **Email 1: Confirmación de Cuenta**
```
Asunto: Confirma tu cuenta en eGarage
Cuándo: Inmediatamente después del registro
Propósito: Verificar email real

Contenido:
- Saludo personalizado
- Instrucciones claras
- Link de confirmación (expira en 48h)
- Info de soporte si no solicitó el registro
```

### **Email 2: Comprobante Recibido** (Solo Chile)
```
Asunto: Comprobante recibido - Verificación en proceso
Cuándo: Después de subir comprobante
Propósito: Confirmar recepción, dar tranquilidad

Contenido:
- Confirmación de recepción
- Tiempo estimado de verificación (24-48h)
- Qué esperar a continuación
- Datos del pago (plan, monto)
```

### **Email 3: Pago Confirmado**
```
Asunto: ¡Tu suscripción a eGarage está activa!
Cuándo: Después de aprobar pago (Chile) o pago exitoso (USA)
Propósito: Notificar activación

Contenido:
- Celebración del pago
- Detalles del plan
- Fecha de vencimiento/renovación
- Link directo al dashboard
- Datos de contacto soporte
```

### **Email 4: Recordatorio de Vencimiento**
```
Asunto: Tu suscripción vence en 7 días
Cuándo: 7 días antes del vencimiento
Propósito: Evitar pérdida de acceso

Contenido:
- Fecha de vencimiento
- Instrucciones para renovar
- Link directo a página de pago
```

### **Email 5: Suscripción Vencida**
```
Asunto: Tu suscripción a eGarage ha vencido
Cuándo: El día del vencimiento
Propósito: Invitar a renovar

Contenido:
- Información de vencimiento
- Qué sucede con los datos (no se borran)
- Tiempo de gracia (ej: 15 días)
- Botón para renovar
```

---

## 🔒 **SEGURIDAD Y VALIDACIONES**

### **Registro:**
```
✅ Email único (no duplicados)
✅ Username único
✅ Contraseña segura (min 8 caracteres)
✅ Token de confirmación único y temporal
✅ Links de confirmación de un solo uso
```

### **Pago:**
```
✅ Verificación manual en Chile (admin revisa comprobante)
✅ Verificación automática en USA (PayPal API)
✅ Estado del pago rastreable
✅ Historial de pagos por empresa
✅ No se activa suscripción sin pago confirmado
```

### **Acceso:**
```
✅ Sin confirmación de email → No puede hacer login
✅ Sin pago confirmado (planes pagados) → No tiene acceso
✅ Suscripción vencida → Acceso de solo lectura
```

---

## 🛠️ **QUÉ FALTA IMPLEMENTAR**

### **Para Producción:**

#### **1. Confirmación de Email** ⚠️ CRÍTICO
```python
# gestion_taller/settings.py
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'  # ← Cambiar esto
ACCOUNT_EMAIL_REQUIRED = True
```

#### **2. Templates de Email** 📧
```
Crear:
- templates/account/email/email_confirmation_subject.txt
- templates/account/email/email_confirmation_message.txt
- templates/email/comprobante_recibido.html
- templates/email/pago_confirmado.html
- templates/email/recordatorio_vencimiento.html
- templates/email/suscripcion_vencida.html
```

#### **3. Backend de Email** ✉️
```python
# Configuración actual (settings.py):
EMAIL_BACKEND = 'taller.backends.egarage_email.EgarageEmailBackend'
EMAIL_HOST = 'srv24.cpanelhost.cl'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_HOST_USER = 'subcription@egarage.cl'
EMAIL_HOST_PASSWORD = '***'

# ✅ Ya está configurado, solo activar verificación
```

#### **4. Notificaciones Admin** 🔔
```python
# Crear: taller/signals.py
@receiver(post_save, sender=PagoPendiente)
def notificar_admin_pago_nuevo(sender, instance, created, **kwargs):
    if created and instance.estado == 'pendiente':
        # Enviar email a admin
        send_mail(
            subject='🔔 Nuevo Pago Pendiente',
            message=f'Empresa: {instance.empresa.nombre_taller}\nMonto: {instance.monto}',
            from_email='noreply@egarage.cl',
            recipient_list=['mauricioatlanta@gmail.com'],
        )
```

#### **5. Envío de Email al Aprobar Pago** ✅
```python
# Actualizar: taller/models/pago.py
def aprobar_pago(self, admin_user):
    # ... código actual ...
    
    # AGREGAR:
    from django.core.mail import send_mail
    
    send_mail(
        subject='✅ ¡Tu pago ha sido confirmado!',
        message=f'Hola {self.empresa.user.first_name}, tu suscripción está activa.',
        from_email='subcription@egarage.cl',
        recipient_list=[self.empresa.email],
        html_message=render_to_string('email/pago_confirmado.html', {
            'empresa': self.empresa,
            'plan': self.plan,
            'fecha_fin': self.empresa.fecha_fin,
        })
    )
```

#### **6. Webhook de PayPal** 🔌
```python
# Crear: taller/views_extra/paypal_webhook.py
@csrf_exempt
def paypal_webhook(request):
    # Verificar firma de PayPal
    # Procesar evento (payment.sale.completed)
    # Activar suscripción
    # Enviar email de confirmación
    pass
```

---

## 📊 **COMPARACIÓN ACTUAL vs IDEAL**

| Aspecto | Actual (Dev) | Ideal (Prod) |
|---------|--------------|--------------|
| **Confirmación Email** | ❌ No | ✅ Sí, obligatorio |
| **Login sin confirmar** | ✅ Sí | ❌ No |
| **Trial inmediato** | ✅ Sí | ⏳ Después de confirmar |
| **Email bienvenida** | ❌ No | ✅ Sí |
| **Email comprobante recibido** | ❌ No | ✅ Sí (Chile) |
| **Email pago confirmado** | ❌ No | ✅ Sí |
| **Notificación a admin** | ❌ No | ✅ Sí |
| **Recordatorio vencimiento** | ❌ No | ✅ Sí (7 días antes) |
| **PayPal webhook** | ❌ No | ✅ Sí |
| **Verificación manual Chile** | ✅ Sí (admin) | ✅ Sí (admin) |
| **Verificación auto USA** | ⚠️ Parcial | ✅ Completa |

---

## 🎯 **PLAN DE IMPLEMENTACIÓN**

### **Fase 1: Email Básico** (1-2 días)
```
✅ Activar ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
✅ Crear templates de confirmación
✅ Probar flujo de confirmación
✅ Email de bienvenida al confirmar
```

### **Fase 2: Emails de Pago** (1 día)
```
✅ Email: Comprobante recibido (Chile)
✅ Email: Pago confirmado (ambos países)
✅ Notificación a admin (pago nuevo)
```

### **Fase 3: Recordatorios** (1 día)
```
✅ Email: 7 días antes de vencer
✅ Email: Día de vencimiento
✅ Comando cron: python manage.py enviar_recordatorios
```

### **Fase 4: PayPal Webhook** (1-2 días)
```
✅ Endpoint webhook
✅ Verificación de firma
✅ Activación automática
✅ Pruebas en sandbox
```

---

## 🧪 **TESTING**

### **Test 1: Registro con Email**
```
1. Registrarse con email real
2. Verificar que NO puede hacer login sin confirmar
3. Recibir email de confirmación
4. Hacer clic en link
5. Verificar que AHORA SÍ puede hacer login
```

### **Test 2: Pago Chile**
```
1. Registrarse con plan mensual
2. Confirmar email
3. Subir comprobante falso
4. Verificar email de "comprobante recibido"
5. Admin aprueba
6. Verificar email de "pago confirmado"
7. Login y verificar acceso
```

### **Test 3: Pago USA**
```
1. Registrarse con monthly plan
2. Confirmar email
3. Pagar con PayPal sandbox
4. Verificar activación automática
5. Verificar email de confirmación
6. Login y verificar acceso
```

---

## ✅ **RESUMEN**

### **ACTUAL (Desarrollo):**
```
❌ Sin confirmación de email
✅ Login inmediato
✅ Trial funciona bien
⚠️ Planes pagados necesitan pago manual
❌ No hay emails automáticos
```

### **IDEAL (Producción):**
```
✅ Confirmación de email obligatoria
✅ Proceso profesional y seguro
✅ Emails en cada paso
✅ Notificaciones a admin
✅ Recordatorios de vencimiento
✅ PayPal automático
```

---

## 🚀 **¿QUIERES QUE IMPLEMENTE EL SISTEMA COMPLETO DE EMAILS?**

Puedo implementar:
1. ✅ Activar confirmación de email
2. ✅ Crear templates de emails (6 tipos)
3. ✅ Sistema de notificaciones
4. ✅ Webhook PayPal
5. ✅ Recordatorios automáticos

**¿Comenzamos con Fase 1 (Email básico)?** 🎯

---

**Creado**: 26 de octubre de 2025, 23:55 hrs

