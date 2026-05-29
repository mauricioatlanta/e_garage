# Password Reset y Account Enumeration Protection

## 🎯 Comportamiento Correcto del Sistema

### ✅ Estado Actual: FUNCIONANDO CORRECTAMENTE

El sistema de password reset está implementado correctamente con protección contra enumeración de cuentas.

---

## 🔐 Account Enumeration Protection

### ¿Qué es?

Es una medida de seguridad estándar que **evita que atacantes descubran qué emails están registrados** en el sistema.

### ¿Cómo funciona?

Cuando un usuario intenta resetear la contraseña:

#### Caso 1: Email EXISTE en la base de datos
```
Usuario ingresa: mauricioatlanta@gmail.com
Sistema verifica: ✅ Usuario existe
Acción: Envía email con link de reset
Template: password_reset_key_message.txt
```

#### Caso 2: Email NO EXISTE en la base de datos
```
Usuario ingresa: noexiste@example.com
Sistema verifica: ❌ Usuario NO existe
Acción: Envía email informativo (no link de reset)
Template: account_inactive_signup_message.txt
Contenido: "No tenemos constancia de dicha cuenta"
          "Puedes registrarte aquí: /accounts/signup/"
```

---

## 📧 Templates de Email

### 1. Password Reset (usuario existe)
**Archivo:** `templates/account/email/password_reset_key_message.txt`

```
¡Hola!

Has solicitado restablecer tu contraseña.
Haz clic en el siguiente enlace:

{{ password_reset_url }}

Si no solicitaste esto, ignora este email.
```

### 2. Account Inactive / Signup (usuario NO existe)
**Archivo:** `templates/account/email/account_inactive_signup_message.txt`

```
¡Hola de parte de eGarage!

Está recibiendo este correo electrónico porque usted, u otra persona, 
intentó acceder a una cuenta con email {{ email }}.

Sin embargo, no tenemos constancia de dicha cuenta en nuestra base de datos.

Este correo puede ser ignorado con seguridad si usted no inició esta acción.

Si ha sido usted, puede registrarse para obtener una cuenta utilizando 
el siguiente enlace:

{{ signup_url }}

¡Gracias por usar eGarage!
www.egarage.cl
```

---

## 🧪 Verificar si un Usuario Existe

### Comando de verificación:

```bash
python manage.py shell -c "
from django.contrib.auth import get_user_model
from allauth.account.models import EmailAddress

email = 'mauricioatlanta@gmail.com'

print(f'USER_COUNT={get_user_model().objects.filter(email__iexact=email).count()}')
print(f'EMAILADDRESS_COUNT={EmailAddress.objects.filter(email__iexact=email).count()}')
"
```

### Resultado esperado:

**Usuario EXISTE:**
```
USER_COUNT=1
EMAILADDRESS_COUNT=1
```

**Usuario NO EXISTE:**
```
USER_COUNT=0
EMAILADDRESS_COUNT=0
```

---

## 🛠️ Crear Usuario Correctamente

### Opción A: Django Admin
1. Ir a `/admin/`
2. Users → Add user
3. Completar datos
4. Guardar

### Opción B: Shell (recomendado para desarrollo)

```python
python manage.py shell

from django.contrib.auth import get_user_model
from allauth.account.models import EmailAddress

User = get_user_model()

# Crear usuario
user = User.objects.create_user(
    username="mauricio",
    email="mauricioatlanta@gmail.com",
    password="test123"
)

# IMPORTANTE: Crear EmailAddress para Allauth
EmailAddress.objects.create(
    user=user,
    email=user.email,
    primary=True,
    verified=True
)

print(f"✅ Usuario creado: {user.email}")
```

---

## 🌍 Redirección de Rutas /accounts/

### Problema Original

Las rutas `/accounts/*` sin prefijo de país causaban inconsistencia:

```
/accounts/password/reset/  → País: None ❌
```

### Solución Implementada

**Middleware:** `taller.middleware.force_accounts_to_cl.ForceAccountsToCLMiddleware`

**Comportamiento:**

```python
# Antes
/accounts/login/           → ❌ Sin país
/accounts/password/reset/  → ❌ Sin país
/accounts/signup/          → ❌ Sin país

# Después (automático)
/accounts/login/           → /cl/es/accounts/login/
/accounts/password/reset/  → /cl/es/accounts/password/reset/
/accounts/signup/          → /us/en/accounts/signup/
```

**Lógica de país:**
1. Query param `?country=us` → `/us/en/accounts/...`
2. Cookie `country=cl` → `/cl/es/accounts/...`
3. Usuario autenticado → país de su empresa
4. Default → `/cl/es/accounts/...`

---

## ⚙️ Configuración (NO recomendado cambiar)

### Desactivar Account Enumeration Protection

```python
# settings.py
ACCOUNT_PREVENT_ENUMERATION = False
```

⚠️ **NO RECOMENDADO EN PRODUCCIÓN**

Esto haría que el sistema:
- Siempre envíe email de reset (incluso si no existe)
- Permita a atacantes descubrir emails registrados
- Viole mejores prácticas de seguridad

---

## 🐛 Troubleshooting

### Problema: "Recibo email de signup en vez de password reset"

**Causa:** El email NO existe en la base de datos.

**Solución:**
1. Verificar que el usuario existe (ver comando arriba)
2. Si no existe, crearlo correctamente
3. Asegurar que existe registro en `EmailAddress` de Allauth

### Problema: "El link de reset no funciona"

**Verificar:**
1. Usuario existe: ✅
2. EmailAddress existe: ✅
3. Email verificado: `verified=True`
4. Usuario activo: `is_active=True`

---

## 📊 Estado del Sistema

| Componente | Estado | Notas |
|------------|--------|-------|
| Password Reset | ✅ CORRECTO | Funcionando según estándar |
| Allauth | ✅ CORRECTO | Account enumeration protection activo |
| Adapter | ✅ CORRECTO | Redirecciones multi-país OK |
| Templates | ✅ CORRECTO | Ambos templates implementados |
| Middleware | ✅ CORRECTO | Fuerza rutas con país |

---

## 🔗 Referencias

- [OWASP - User Enumeration](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/03-Identity_Management_Testing/04-Testing_for_Account_Enumeration_and_Guessable_User_Account)
- [Django Allauth - Account Enumeration](https://django-allauth.readthedocs.io/en/latest/configuration.html)
- [Security Best Practices](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)

---

**Última actualización:** 2026-03-29  
**Autor:** Sistema eGarage  
**Estado:** ✅ Documentación completa y verificada
