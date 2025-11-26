# 📋 Reporte: Mecánica de Registro en eGarage

**Fecha:** Diciembre 2024  
**Sistema:** eGarage - Sistema Multi-País  
**Versión:** Análisis Completo del Sistema de Registro

---

## 📊 Resumen Ejecutivo

eGarage implementa un **sistema de registro multi-país** que soporta actualmente **8 países**: 🇺🇸 Estados Unidos (US), 🇨🇱 Chile (CL), 🇲🇽 México (MX), 🇵🇪 Perú (PE), 🇨🇴 Colombia (CO), 🇪🇨 Ecuador (EC), 🇧🇷 Brasil (BR), y 🇻🇪 Venezuela (VE). El sistema ofrece **múltiples métodos de registro** adaptados a diferentes necesidades de negocio, desde registro gratuito hasta suscripciones pagadas con períodos de prueba.

---

## 🌍 Países Soportados

### Países Disponibles

| País | Código | Moneda | Idioma | Zona Horaria Default | Estado |
|------|--------|--------|--------|---------------------|--------|
| 🇺🇸 Estados Unidos | `US` | USD | Inglés (EN) | America/New_York | ✅ Completo |
| 🇨🇱 Chile | `CL` | CLP | Español (ES) | America/Santiago | ✅ Completo |
| 🇲🇽 México | `MX` | MXN | Español (ES) | America/Mexico_City | ✅ Completo |
| 🇵🇪 Perú | `PE` | PEN | Español (ES) | America/Lima | ⚠️ Parcial |
| 🇨🇴 Colombia | `CO` | COP | Español (ES) | America/Bogota | ⚠️ Parcial |
| 🇪🇨 Ecuador | `EC` | USD | Español (ES) | America/Guayaquil | ⚠️ Parcial |
| 🇧🇷 Brasil | `BR` | BRL | Portugués (PT) | America/Sao_Paulo | ⚠️ Parcial |
| 🇻🇪 Venezuela | `VE` | VES | Español (ES) | America/Caracas | ⚠️ Parcial |

**Nota:** Los países marcados como "Parcial" tienen soporte en el modelo de ubicaciones (`Estado` y `Ciudad`) pero pueden requerir configuración adicional en el modelo `Empresa` y en los formularios de registro.

### Configuración por País

Cada país tiene configuraciones específicas:
- **Moneda:** Se asigna automáticamente según el país seleccionado
- **Idioma:** Se configura automáticamente (EN para US, ES para CL/MX/PE/CO/EC/VE, PT para BR)
- **Zona Horaria:** Se asigna según el país
- **Formato de Precios:** 
  - US, MX, PE, CO, EC: 2 decimales ($20.00)
  - CL: 0 decimales ($20.000)
  - BR: 2 decimales (R$ 20,00)
  - VE: 2 decimales (Bs. 20,00)

---

## 🔄 Sistemas de Registro Disponibles

eGarage implementa **4 sistemas de registro diferentes**, cada uno diseñado para casos de uso específicos:

### 1. **CustomSignupView** (Registro Universal con Allauth)

**Ubicación:** `taller/views_extra/custom_signup.py`  
**Formulario:** `taller/forms/custom_signup.py`  
**URL:** `/accounts/signup/`

#### Características:
- ✅ Usa Django Allauth para gestión de autenticación
- ✅ Selección de país en el formulario (US, CL, MX, PE, CO, EC, BR, VE)
- ✅ Verificación de email configurable
- ✅ Login automático si no requiere verificación de email
- ✅ Redirección automática según país después del registro

#### Flujo de Registro:

```
1. Usuario visita /accounts/signup/
   ↓
2. Completa formulario:
   - Email (requerido)
   - Username
   - Password (confirmación)
   - País (US, CL, MX, PE, CO, EC, BR, VE)
   ↓
3. Sistema valida datos
   ↓
4. Crea usuario en Django
   ↓
5. Configura idioma según país:
   - CL, MX, PE, CO, EC, VE → Español (ES)
   - US → Inglés (EN)
   - BR → Portugués (PT)
   ↓
6. Verifica si requiere verificación de email:
   - Si ACCOUNT_EMAIL_VERIFICATION = "mandatory":
     → Envía email de confirmación
     → Redirige a página de verificación
   - Si ACCOUNT_EMAIL_VERIFICATION = "none":
     → Login automático
     → Redirige a dashboard del país
```

#### Campos del Formulario:

```python
- email: EmailField (requerido)
- username: CharField
- password1: PasswordInput
- password2: PasswordInput (confirmación)
- country: ChoiceField (US, CL, MX, PE, CO, EC, BR, VE)
```

#### Redirecciones Post-Registro:

- **Chile (CL):** `/cl/centro-operaciones/` (chile:centro_operaciones)
- **USA (US):** `/us/centro-operaciones-espacial/` (usa:centro_operaciones_espacial)
- **México (MX):** `/mx/centro-operaciones/` (similar a Chile)
- **Perú (PE):** `/pe/centro-operaciones/` (configuración pendiente)
- **Colombia (CO):** `/co/centro-operaciones/` (configuración pendiente)
- **Ecuador (EC):** `/ec/centro-operaciones/` (configuración pendiente)
- **Brasil (BR):** `/br/centro-operaciones/` (configuración pendiente)
- **Venezuela (VE):** `/ve/centro-operaciones/` (configuración pendiente)

---

### 2. **Registro Gratuito** (`registro_gratuito`)

**Ubicación:** `scripts/onboarding_views.py`  
**URL:** `/registro-gratuito/` o `/onboarding/registro-gratuito/`

#### Características:
- ✅ Registro completamente gratuito e ilimitado
- ✅ Creación automática de empresa
- ✅ Login automático inmediato
- ✅ Plan "gratuito" asignado automáticamente
- ✅ Templates diferentes según país (US vs CL)

#### Flujo de Registro:

```
1. Usuario visita /registro-gratuito/
   ↓
2. Sistema detecta país desde URL:
   - /us/... → USA
   - /cl/... → Chile
   ↓
3. Usuario completa formulario (JSON POST):
   - nombre_taller
   - email
   - password
   - nombre_usuario (opcional, usa email si no se proporciona)
   ↓
4. Validaciones:
   - Verifica que todos los campos estén presentes
   - Verifica que el email no exista
   ↓
5. Crea usuario:
   - username = email
   - email = email
   - password = password
   - first_name = nombre_usuario
   ↓
6. Crea empresa automáticamente:
   - user = usuario creado
   - nombre_taller = nombre_taller
   - email = email
   - plan = "gratuito"
   - suscripcion_activa = True
   ↓
7. Crea perfil de usuario (si existe modelo):
   - usuario = usuario
   - empresa = empresa
   - tipo_usuario = "admin"
   ↓
8. Login automático
   ↓
9. Redirige a /bienvenida/
```

#### Templates por País:

- **USA:** `taller/us/en/onboarding/registro_gratuito.html`
- **Chile:** `taller/cl/es/onboarding/registro_gratuito.html`

---

### 3. **Registro con Planes** (`registro`)

**Ubicación:** `taller/views_extra/suscripcion.py`  
**URL:** `/registro/`

#### Características:
- ✅ Registro con selección de plan (trial, mensual, semestral, anual)
- ✅ Soporte para prueba gratuita (trial) con código de activación
- ✅ Soporte para suscripciones pagadas
- ✅ Validación de prueba gratuita (evita duplicados)
- ✅ Envío de emails con instrucciones

#### Tipos de Registro:

##### A. Registro Trial (Prueba Gratuita)

```
1. Usuario selecciona tipo_registro = "trial"
   ↓
2. Completa formulario:
   - email
   - telefono
   - nombre_taller
   - plan = "trial"
   - pais
   ↓
3. Validaciones:
   - Verifica que email no exista
   - Valida que no haya usado prueba antes (email + teléfono)
   ↓
4. Crea usuario
   ↓
5. Crea empresa:
   - plan = "trial"
   - pais = pais seleccionado
   ↓
6. Crea TallerInfo:
   - ha_usado_prueba = True
   ↓
7. Genera código de activación (6 dígitos)
   ↓
8. Crea TrialRegistro:
   - codigo = código generado
   - expira_en = ahora + 24 horas
   - ip, user_agent guardados
   ↓
9. Envía email con:
   - Código de activación
   - URL de activación según país
   ↓
10. Muestra página "registro_enviado.html"
```

**URLs de Activación por País:**
- **US:** `/us/activar-trial/`
- **MX:** `/mx/es/activar-trial/`
- **CL:** `/cl/es/activar-trial/`
- **PE:** `/pe/es/activar-trial/` (configuración pendiente)
- **CO:** `/co/es/activar-trial/` (configuración pendiente)
- **EC:** `/ec/es/activar-trial/` (configuración pendiente)
- **BR:** `/br/pt/activar-trial/` (configuración pendiente)
- **VE:** `/ve/es/activar-trial/` (configuración pendiente)

**Proceso de Activación:**

```
1. Usuario recibe email con código
   ↓
2. Visita URL de activación
   ↓
3. Ingresa email y código
   ↓
4. Sistema valida:
   - Código existe y no ha expirado (24h)
   - Email coincide
   ↓
5. Activa suscripción trial
   ↓
6. Invalida código usado
   ↓
7. Muestra página de activación exitosa
```

##### B. Registro con Pago

```
1. Usuario selecciona tipo_registro = "pago"
   ↓
2. Completa formulario:
   - email
   - telefono
   - nombre_taller
   - plan = "mensual" | "semestral" | "anual"
   - pais
   ↓
3. Crea usuario y empresa
   ↓
4. Envía email con instrucciones de pago:
   - Monto según plan y país
   - Cuenta bancaria según país
   - Email de soporte para enviar comprobante
   ↓
5. Muestra página con información de pago
```

**Precios por País y Plan:**

| Plan | USA (USD) | Chile (CLP) | México (MXN) | Perú (PEN) | Colombia (COP) | Ecuador (USD) | Brasil (BRL) | Venezuela (VES) |
|------|-----------|-------------|--------------|------------|----------------|---------------|--------------|-----------------|
| Mensual | $20.00 | $20.000 | $399 | * | * | * | * | * |
| Semestral | $110.00 | $110.000 | $2,199 | * | * | * | * | * |
| Anual | $200.00 | $200.000 | $3,990 | * | * | * | * | * |

*Nota: Los precios para PE, CO, EC, BR y VE están pendientes de configuración.*

---

### 4. **Registro Unificado** (`registro_unificado`)

**Ubicación:** `taller/registro_views.py`  
**URL:** `/registro-unificado/`

#### Características:
- ✅ Sistema unificado que maneja trial y pago
- ✅ Generación de códigos de instalación
- ✅ Envío de emails automático

#### Flujo:

Similar al sistema de registro con planes, pero con una interfaz unificada que permite seleccionar entre trial y pago en el mismo formulario.

---

## 🔐 Verificación de Email

### Configuración

El sistema usa Django Allauth para verificación de email. La configuración se encuentra en `settings.py`:

```python
ACCOUNT_EMAIL_VERIFICATION = os.getenv(
    "ACCOUNT_EMAIL_VERIFICATION",
    "mandatory",  # 🔒 Siempre obligatorio en producción
)
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 2
```

### Comportamiento

- **Si `ACCOUNT_EMAIL_VERIFICATION = "mandatory"`:**
  - Usuario debe verificar email antes de usar la cuenta
  - Se envía email de confirmación automáticamente
  - Usuario no puede hacer login hasta verificar
  - Redirige a página de verificación enviada

- **Si `ACCOUNT_EMAIL_VERIFICATION = "none"`:**
  - No se requiere verificación
  - Login automático después del registro
  - Redirige directamente al dashboard

---

## 🌐 Detección de País

El sistema usa una **jerarquía de detección de país** con múltiples niveles:

### Orden de Prioridad:

```
1️⃣ Prefijo de URL (/us/, /cl/, /mx/, /pe/, /co/, /ec/, /br/, /ve/)     ← MÁS PRIORITARIO
      ↓ Si no hay prefijo
2️⃣ Empresa del usuario (campo pais)      ← Para usuarios autenticados
      ↓ Si no está autenticado
3️⃣ Parámetro en URL (?country=US)
      ↓ Si no hay parámetro
4️⃣ País por defecto (CL - Chile)        ← MENOS PRIORITARIO
```

### Implementación

**Middleware:** `CountryContextMiddleware`, `CountryMiddleware`  
**Modelo:** Campo `pais` en modelo `Empresa`

```python
# Ejemplo de detección
if request.path.startswith('/us/'):
    country = 'US'
elif request.path.startswith('/cl/'):
    country = 'CL'
elif request.path.startswith('/mx/'):
    country = 'MX'
elif request.path.startswith('/pe/'):
    country = 'PE'
elif request.path.startswith('/co/'):
    country = 'CO'
elif request.path.startswith('/ec/'):
    country = 'EC'
elif request.path.startswith('/br/'):
    country = 'BR'
elif request.path.startswith('/ve/'):
    country = 'VE'
elif request.user.is_authenticated:
    country = request.user.empresa.pais
else:
    country = 'CL'  # Default
```

---

## 📝 Modelos de Datos

### Modelo: `Empresa`

**Ubicación:** `taller/models/empresa.py`

```python
class Empresa(models.Model):
    user = OneToOneField(User)
    nombre_taller = CharField(max_length=100)
    pais = CharField(max_length=2, choices=[
        ('CL', 'Chile'),
        ('US', 'United States'),
        ('MX', 'México'),
        ('PE', 'Perú'),
        ('CO', 'Colombia'),
        ('EC', 'Ecuador'),
        ('BR', 'Brasil'),
        ('VE', 'Venezuela'),
    ])
    plan = CharField(choices=[
        ('trial', 'Prueba Gratuita'),
        ('basic', 'Plan Básico'),
        ('premium', 'Plan Premium'),
        ('enterprise', 'Plan Empresarial'),
    ])
    moneda = CharField(choices=[('CLP', 'CLP'), ('USD', 'USD'), ('MXN', 'MXN')])
    zona_horaria = CharField(max_length=50)
    suscripcion_activa = BooleanField(default=True)
    fecha_inicio = DateTimeField(default=timezone.now)
    fecha_fin = DateTimeField(null=True, blank=True)
    dias_prueba = PositiveIntegerField(default=30)
```

**Asignación Automática:**
- Moneda se asigna según país:
  - US, EC: USD
  - CL: CLP
  - MX: MXN
  - PE: PEN
  - CO: COP
  - BR: BRL
  - VE: VES
- Zona horaria se asigna según país
- Plan se asigna según tipo de registro

### Modelo: `TrialRegistro`

**Ubicación:** `taller/models/trial.py`

```python
class TrialRegistro(models.Model):
    nombre = CharField(max_length=100)
    email = EmailField()
    telefono = CharField(max_length=32)
    codigo = CharField(max_length=12)  # Código de activación
    ip = GenericIPAddressField()
    user_agent = CharField(max_length=255)
    creado_en = DateTimeField()
    expira_en = DateTimeField()  # 24 horas después de creación
    user = ForeignKey(User, null=True)
```

---

## 🔄 Flujos Completos por País

### 🇺🇸 Estados Unidos (US)

#### Registro desde Landing Page:

```
1. Usuario visita: https://egarage.com/
   ↓
2. Selecciona: 🇺🇸 United States
   ↓
3. Redirige a: /us/
   ↓
4. Hace clic en "Sign Up"
   ↓
5. URL: /us/accounts/signup/ o /accounts/signup/?country=US
   ↓
6. Completa formulario:
   - Email: user@example.com
   - Username: user
   - Password: ********
   - Country: 🇺🇸 United States
   ↓
7. Sistema crea:
   - User: user@example.com
   - Empresa: pais="US", moneda="USD", idioma="en"
   ↓
8. Si requiere verificación:
   - Envía email de confirmación
   - Redirige a página de verificación
   ↓
9. Usuario verifica email
   ↓
10. Redirige a: /us/centro-operaciones-espacial/
```

**Características:**
- Idioma: Inglés (EN)
- Moneda: USD
- Precios: $20.00, $110.00, $200.00
- IVA: 0% (no aplica)
- Zona horaria: America/New_York (default)

---

### 🇨🇱 Chile (CL)

#### Registro desde Landing Page:

```
1. Usuario visita: https://egarage.com/
   ↓
2. Selecciona: 🇨🇱 Chile
   ↓
3. Redirige a: /cl/
   ↓
4. Hace clic en "Registrarse"
   ↓
5. URL: /cl/accounts/signup/ o /accounts/signup/?country=CL
   ↓
6. Completa formulario:
   - Email: usuario@example.cl
   - Username: usuario
   - Password: ********
   - País: 🇨🇱 Chile
   ↓
7. Sistema crea:
   - User: usuario@example.cl
   - Empresa: pais="CL", moneda="CLP", idioma="es"
   ↓
8. Si requiere verificación:
   - Envía email de confirmación
   - Redirige a página de verificación
   ↓
9. Usuario verifica email
   ↓
10. Redirige a: /cl/centro-operaciones/
```

**Características:**
- Idioma: Español (ES)
- Moneda: CLP
- Precios: $20.000, $110.000, $200.000
- IVA: 19% (aplicable)
- Zona horaria: America/Santiago

---

### 🇲🇽 México (MX)

#### Registro desde Landing Page:

```
1. Usuario visita: https://egarage.com/
   ↓
2. Selecciona: 🇲🇽 México
   ↓
3. Redirige a: /mx/
   ↓
4. Hace clic en "Registrarse"
   ↓
5. URL: /mx/accounts/signup/ o /accounts/signup/?country=MX
   ↓
6. Completa formulario:
   - Email: usuario@example.mx
   - Username: usuario
   - Password: ********
   - País: 🇲🇽 México
   ↓
7. Sistema crea:
   - User: usuario@example.mx
   - Empresa: pais="MX", moneda="MXN", idioma="es"
   ↓
8. Si requiere verificación:
   - Envía email de confirmación
   - Redirige a página de verificación
   ↓
9. Usuario verifica email
   ↓
10. Redirige a: /mx/centro-operaciones/
```

**Características:**
- Idioma: Español (ES)
- Moneda: MXN
- Precios: $399, $2,199, $3,990
- IVA: Configuración pendiente
- Zona horaria: America/Mexico_City (default)

---

### 🇵🇪 Perú (PE)

**Características:**
- Idioma: Español (ES)
- Moneda: PEN (Soles Peruanos)
- Precios: Pendientes de configuración
- IVA: Configuración pendiente
- Zona horaria: America/Lima
- Estado: ⚠️ Soporte parcial (modelo de ubicaciones disponible)

---

### 🇨🇴 Colombia (CO)

**Características:**
- Idioma: Español (ES)
- Moneda: COP (Pesos Colombianos)
- Precios: Pendientes de configuración
- IVA: Configuración pendiente
- Zona horaria: America/Bogota
- Estado: ⚠️ Soporte parcial (modelo de ubicaciones disponible)

---

### 🇪🇨 Ecuador (EC)

**Características:**
- Idioma: Español (ES)
- Moneda: USD (Dólares Estadounidenses)
- Precios: Pendientes de configuración
- IVA: Configuración pendiente
- Zona horaria: America/Guayaquil
- Estado: ⚠️ Soporte parcial (modelo de ubicaciones disponible)

---

### 🇧🇷 Brasil (BR)

**Características:**
- Idioma: Portugués (PT)
- Moneda: BRL (Reales Brasileños)
- Precios: Pendientes de configuración
- Impuestos: ICMS (configuración pendiente)
- Zona horaria: America/Sao_Paulo
- Estado: ⚠️ Soporte parcial (modelo de ubicaciones disponible, incluye campos IBGE)

---

### 🇻🇪 Venezuela (VE)

**Características:**
- Idioma: Español (ES)
- Moneda: VES (Bolívares Soberanos)
- Precios: Pendientes de configuración
- IVA: Configuración pendiente
- Zona horaria: America/Caracas
- Estado: ⚠️ Soporte parcial (modelo de ubicaciones disponible)

---

## 🛡️ Validaciones y Seguridad

### Validaciones de Email

1. **Email único:** No se permite duplicar emails
2. **Formato válido:** Validación de formato de email
3. **Normalización:** Email se normaliza a minúsculas antes de guardar

### Validaciones de Usuario

1. **Username único:** No se permite duplicar usernames
2. **Password:** Validación de fortaleza (configurada en Django)
3. **Email requerido:** Campo obligatorio en todos los formularios

### Validaciones de Prueba Gratuita

1. **Email + Teléfono:** No se permite usar prueba más de una vez con el mismo email o teléfono
2. **Código de activación:** Expira después de 24 horas
3. **Un código por usuario:** Cada código solo puede usarse una vez

### Seguridad

- **Transacciones atómicas:** Uso de `transaction.atomic()` para garantizar consistencia
- **IP y User-Agent:** Se guardan para auditoría en registros trial
- **Códigos seguros:** Códigos de activación generados aleatoriamente
- **Verificación de email:** Obligatoria en producción

---

## 📧 Emails Enviados

### 1. Email de Confirmación (Allauth)

**Cuándo:** Después de registro con `ACCOUNT_EMAIL_VERIFICATION = "mandatory"`  
**Template:** `templates/account/email/email_confirmation_message.html`  
**Contenido:**
- Link de confirmación
- Instrucciones para activar cuenta
- Información de bienvenida

### 2. Email de Código de Activación (Trial)

**Cuándo:** Después de registro trial  
**Contenido:**
- Código de activación (6 dígitos)
- URL de activación según país
- Instrucciones de uso
- Tiempo de expiración (24 horas)

### 3. Email de Instrucciones de Pago

**Cuándo:** Después de registro con plan pagado  
**Contenido:**
- Monto a pagar según plan y país
- Cuenta bancaria según país
- Concepto de pago
- Email de soporte para enviar comprobante
- Instrucciones de activación post-pago

---

## 🔗 URLs de Registro

### URLs Principales

| URL | Descripción | País |
|-----|-------------|------|
| `/accounts/signup/` | Registro universal (Allauth) | Todos |
| `/registro/` | Registro con planes | Todos |
| `/registro-gratuito/` | Registro gratuito | Todos |
| `/registro-unificado/` | Registro unificado | Todos |
| `/us/accounts/signup/` | Registro USA | US |
| `/cl/accounts/signup/` | Registro Chile | CL |
| `/mx/accounts/signup/` | Registro México | MX |
| `/pe/accounts/signup/` | Registro Perú | PE |
| `/co/accounts/signup/` | Registro Colombia | CO |
| `/ec/accounts/signup/` | Registro Ecuador | EC |
| `/br/accounts/signup/` | Registro Brasil | BR |
| `/ve/accounts/signup/` | Registro Venezuela | VE |

### URLs de Activación

| URL | Descripción | País |
|-----|-------------|------|
| `/us/activar-trial/` | Activar prueba USA | US |
| `/cl/es/activar-trial/` | Activar prueba Chile | CL |
| `/mx/es/activar-trial/` | Activar prueba México | MX |
| `/pe/es/activar-trial/` | Activar prueba Perú | PE |
| `/co/es/activar-trial/` | Activar prueba Colombia | CO |
| `/ec/es/activar-trial/` | Activar prueba Ecuador | EC |
| `/br/pt/activar-trial/` | Activar prueba Brasil | BR |
| `/ve/es/activar-trial/` | Activar prueba Venezuela | VE |

---

## 🎯 Redirecciones Post-Registro

### Después de Registro Exitoso

| País | Con Verificación Email | Sin Verificación Email |
|------|------------------------|------------------------|
| **US** | `/accounts/email-verification-sent/` → luego `/us/centro-operaciones-espacial/` | `/us/centro-operaciones-espacial/` |
| **CL** | `/accounts/email-verification-sent/` → luego `/cl/centro-operaciones/` | `/cl/centro-operaciones/` |
| **MX** | `/accounts/email-verification-sent/` → luego `/mx/centro-operaciones/` | `/mx/centro-operaciones/` |
| **PE** | `/accounts/email-verification-sent/` → luego `/pe/centro-operaciones/` | `/pe/centro-operaciones/` |
| **CO** | `/accounts/email-verification-sent/` → luego `/co/centro-operaciones/` | `/co/centro-operaciones/` |
| **EC** | `/accounts/email-verification-sent/` → luego `/ec/centro-operaciones/` | `/ec/centro-operaciones/` |
| **BR** | `/accounts/email-verification-sent/` → luego `/br/centro-operaciones/` | `/br/centro-operaciones/` |
| **VE** | `/accounts/email-verification-sent/` → luego `/ve/centro-operaciones/` | `/ve/centro-operaciones/` |

### Después de Activación de Trial

| País | Redirección |
|------|-------------|
| **US** | `/us/dashboard/` |
| **CL** | `/cl/dashboard/` |
| **MX** | `/mx/dashboard/` |
| **PE** | `/pe/dashboard/` |
| **CO** | `/co/dashboard/` |
| **EC** | `/ec/dashboard/` |
| **BR** | `/br/dashboard/` |
| **VE** | `/ve/dashboard/` |

---

## 📊 Comparativa de Sistemas de Registro

| Característica | CustomSignupView | Registro Gratuito | Registro con Planes | Registro Unificado |
|----------------|------------------|-------------------|---------------------|---------------------|
| **Verificación Email** | ✅ Configurable | ❌ No | ❌ No | ❌ No |
| **Login Automático** | ✅ Si no requiere verificación | ✅ Sí | ❌ No | ❌ No |
| **Creación de Empresa** | ⚠️ Manual | ✅ Automática | ✅ Automática | ✅ Automática |
| **Selección de País** | ✅ En formulario | ⚠️ Desde URL | ✅ En formulario | ✅ En formulario |
| **Planes** | ❌ No | ✅ Solo "gratuito" | ✅ Trial/Pago | ✅ Trial/Pago |
| **Código de Activación** | ❌ No | ❌ No | ✅ Solo trial | ✅ Solo trial |
| **Onboarding** | ❌ No | ✅ Sí | ❌ No | ❌ No |

---

## 🔧 Configuración Técnica

### Settings Relevantes

```python
# Autenticación
AUTHENTICATION_BACKENDS = [
    "allauth.account.auth_backends.AuthenticationBackend",
]

# Allauth
ACCOUNT_AUTHENTICATION_METHOD = "username_email"
ACCOUNT_EMAIL_VERIFICATION = "mandatory"  # o "none"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 2

# URLs
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"  # Se sobrescribe por país
```

### Middlewares

```python
MIDDLEWARE = [
    # ... otros middlewares
    'taller.middleware.empresa_middleware.EmpresaMiddleware',
    'taller.middleware.country_context.CountryContextMiddleware',
    'taller.middleware.simple_country_redirect.SimpleCountryRedirectMiddleware',
    'taller.middleware.lang_policy.LanguagePolicyMiddleware',
    # ... otros middlewares
]
```

---

## 📈 Estadísticas y Métricas

### Datos Capturados

1. **Durante Registro:**
   - Email
   - Username
   - País seleccionado
   - IP address (para trial)
   - User-Agent (para trial)
   - Timestamp de registro

2. **Durante Activación Trial:**
   - Email usado
   - Código ingresado
   - Timestamp de activación

3. **Para Análisis:**
   - País de origen
   - Tipo de registro (trial vs pago)
   - Plan seleccionado
   - Método de registro usado

---

## 🐛 Casos Especiales y Manejo de Errores

### Errores Comunes

1. **Email ya existe:**
   - Mensaje: "Ya existe una cuenta con este email"
   - Acción: Usuario debe usar otro email o hacer login

2. **Username ya existe:**
   - Mensaje: "Este username ya está en uso"
   - Acción: Sistema sugiere alternativas

3. **Prueba gratuita ya usada:**
   - Mensaje: "Ya has usado la prueba gratuita"
   - Acción: Usuario debe registrarse con plan pagado

4. **Código de activación inválido:**
   - Mensaje: "Código inválido o expirado"
   - Acción: Usuario debe solicitar nuevo código

5. **Email no verificado:**
   - Mensaje: "Por favor verifica tu email"
   - Acción: Usuario debe hacer clic en link de confirmación

---

## 🚀 Mejoras Futuras Sugeridas

1. **Registro Social:**
   - Integración con Google OAuth
   - Integración con Facebook Login
   - Integración con Apple Sign In

2. **Más Países:**
   - ✅ Perú (PE) - Parcialmente implementado
   - ✅ Colombia (CO) - Parcialmente implementado
   - ✅ Ecuador (EC) - Parcialmente implementado
   - ✅ Brasil (BR) - Parcialmente implementado
   - ✅ Venezuela (VE) - Parcialmente implementado
   - Argentina (AR) - Pendiente
   - Otros países de Latinoamérica - Pendiente

3. **Mejoras de UX:**
   - Validación en tiempo real
   - Sugerencias de username disponibles
   - Indicador de fortaleza de password
   - Autocompletado de país por IP

4. **Analytics:**
   - Tracking de conversión por país
   - Análisis de abandono en formularios
   - Métricas de activación de trial

---

## 📚 Archivos Clave del Sistema

### Vistas
- `taller/views_extra/custom_signup.py` - Registro universal
- `taller/views_extra/suscripcion.py` - Registro con planes
- `scripts/onboarding_views.py` - Registro gratuito
- `taller/registro_views.py` - Registro unificado

### Formularios
- `taller/forms/custom_signup.py` - Formulario universal
- `taller/forms/suscripcion.py` - Formulario con planes

### Modelos
- `taller/models/empresa.py` - Modelo Empresa
- `taller/models/trial.py` - Modelo TrialRegistro
- `taller/models/perfil_usuario.py` - Modelo PerfilUsuario

### Middlewares
- `taller/middleware/country_context.py` - Detección de país
- `taller/middleware/empresa_middleware.py` - Carga de empresa
- `taller/middleware/simple_country_redirect.py` - Redirección por país

### Adapters
- `taller/views_extra/account_adapter.py` - Adaptador Allauth para país

---

## ✅ Checklist de Registro por País

### Estados Unidos (US)
- [x] Formulario en inglés
- [x] Moneda USD
- [x] Precios en formato USD ($20.00)
- [x] Zona horaria US
- [x] Redirección a dashboard USA
- [x] Templates específicos

### Chile (CL)
- [x] Formulario en español
- [x] Moneda CLP
- [x] Precios en formato CLP ($20.000)
- [x] Zona horaria Chile
- [x] Redirección a dashboard Chile
- [x] Templates específicos
- [x] IVA 19%

### México (MX)
- [x] Formulario en español
- [x] Moneda MXN
- [x] Precios en formato MXN ($399)
- [x] Zona horaria México
- [x] Redirección a dashboard México
- [x] Templates específicos
- [ ] IVA configurado (pendiente)

### Perú (PE)
- [x] Modelo de ubicaciones (Estado, Ciudad)
- [ ] Formulario de registro
- [ ] Moneda PEN configurada
- [ ] Precios configurados
- [ ] Zona horaria America/Lima
- [ ] Redirección a dashboard Perú
- [ ] Templates específicos
- [ ] IVA configurado

### Colombia (CO)
- [x] Modelo de ubicaciones (Estado, Ciudad)
- [ ] Formulario de registro
- [ ] Moneda COP configurada
- [ ] Precios configurados
- [ ] Zona horaria America/Bogota
- [ ] Redirección a dashboard Colombia
- [ ] Templates específicos
- [ ] IVA configurado

### Ecuador (EC)
- [x] Modelo de ubicaciones (Estado, Ciudad)
- [ ] Formulario de registro
- [ ] Moneda USD configurada
- [ ] Precios configurados
- [ ] Zona horaria America/Guayaquil
- [ ] Redirección a dashboard Ecuador
- [ ] Templates específicos
- [ ] IVA configurado

### Brasil (BR)
- [x] Modelo de ubicaciones (Estado, Ciudad) con campos IBGE
- [ ] Formulario de registro
- [ ] Moneda BRL configurada
- [ ] Precios configurados
- [ ] Zona horaria America/Sao_Paulo
- [ ] Redirección a dashboard Brasil
- [ ] Templates específicos en portugués
- [ ] ICMS configurado

### Venezuela (VE)
- [x] Modelo de ubicaciones (Estado, Ciudad)
- [ ] Formulario de registro
- [ ] Moneda VES configurada
- [ ] Precios configurados
- [ ] Zona horaria America/Caracas
- [ ] Redirección a dashboard Venezuela
- [ ] Templates específicos
- [ ] IVA configurado

---

## 📞 Soporte y Contacto

Para problemas con el registro:
- **Email de soporte:** subscription@egarage.cl
- **Documentación:** Ver archivos en `/docs/`
- **Logs:** Revisar logs de Django para errores

---

**Documento generado:** Diciembre 2024  
**Última actualización:** Diciembre 2024  
**Versión del sistema:** Análisis completo  
**Estado:** ✅ Sistema funcional en producción

