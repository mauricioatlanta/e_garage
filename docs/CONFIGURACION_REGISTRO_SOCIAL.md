# 🔐 Configuración de Registro Social (Google/Microsoft)

## 📋 Resumen

Guía para configurar registro social con Google y Microsoft usando django-allauth.

## 🎯 Por Qué Registro Social

**Ventajas:**
- ✅ Reducción de fricción (no recordar contraseña)
- ✅ Mayor conversión (menos campos a llenar)
- ✅ Seguridad (autenticación de terceros confiables)
- ✅ B2B: Microsoft es popular en talleres corporativos

## 🔧 Configuración

### 1. Instalar Dependencias

```bash
pip install django-allauth
```

### 2. Configurar Settings

Agregar a `settings.py`:

```python
INSTALLED_APPS = [
    # ...
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.microsoft',  # Office 365
    # ...
]

# Configuración de django-allauth
SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Configuración de cuenta
ACCOUNT_EMAIL_VERIFICATION = 'optional'  # Para trial, usar 'optional'
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False

# Configuración de proveedores sociales
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'APP': {
            'client_id': 'TU_GOOGLE_CLIENT_ID',
            'secret': 'TU_GOOGLE_SECRET',
            'key': ''
        }
    },
    'microsoft': {
        'TENANT': 'common',  # o 'organizations' para solo cuentas corporativas
        'SCOPE': [
            'User.Read',
            'email',
            'profile',
        ],
        'APP': {
            'client_id': 'TU_MICROSOFT_CLIENT_ID',
            'secret': 'TU_MICROSOFT_SECRET',
            'key': ''
        }
    }
}
```

### 3. Configurar URLs

Agregar a `urls.py` principal:

```python
from allauth import urls as allauth_urls

urlpatterns = [
    # ...
    path('accounts/', include(allauth_urls)),
    # ...
]
```

### 4. Obtener Credenciales

#### Google OAuth

1. Ir a [Google Cloud Console](https://console.cloud.google.com/)
2. Crear proyecto
3. Habilitar Google+ API
4. Crear credenciales OAuth 2.0
5. Configurar URIs de redirección:
   - `http://localhost:8000/accounts/google/login/callback/` (desarrollo)
   - `https://egarage.cl/accounts/google/login/callback/` (producción)

#### Microsoft OAuth

1. Ir a [Azure Portal](https://portal.azure.com/)
2. Crear App Registration
3. Configurar Redirect URIs:
   - `http://localhost:8000/accounts/microsoft/login/callback/` (desarrollo)
   - `https://egarage.cl/accounts/microsoft/login/callback/` (producción)
4. Obtener Client ID y Secret

### 5. Integrar con RegistrationService

Modificar `taller/services/registration_service.py` para manejar registro social:

```python
@staticmethod
def register_from_social_account(sociallogin, country='CL', plan_type='trial', request=None):
    """
    Registra usuario desde cuenta social (Google/Microsoft).
    
    Args:
        sociallogin: Objeto SocialLogin de allauth
        country: Código de país
        plan_type: Tipo de plan
        request: HttpRequest
    
    Returns:
        dict: Resultado del registro
    """
    user = sociallogin.user
    email = user.email
    
    # Verificar si ya tiene empresa
    if hasattr(user, 'empresa') and user.empresa:
        return {
            'user': user,
            'empresa': user.empresa,
            'already_registered': True,
        }
    
    # Crear empresa automáticamente
    nombre_taller = user.get_full_name() or f'Taller de {user.username}'
    
    return RegistrationService.register_new_client(
        user_data={
            'email': email,
            'password': None,  # No password en registro social
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username,
        },
        company_data={
            'nombre_taller': nombre_taller,
        },
        plan_type=plan_type,
        country=country,
        skip_email_verification=True,  # ✅ Email ya verificado por Google/Microsoft
        assign_role='Owner',
        request=request
    )
```

### 6. Señal de Allauth

Crear `taller/signals/social_signals.py`:

```python
from allauth.account.signals import user_signed_up
from django.dispatch import receiver
from taller.services import RegistrationService

@receiver(user_signed_up)
def social_account_signed_up(request, user, sociallogin=None, **kwargs):
    """
    Maneja registro desde cuenta social.
    Si viene de Google/Microsoft, crear empresa automáticamente.
    """
    if sociallogin:
        # Detectar país desde request
        country = getattr(request, 'country', 'CL')
        
        # Registrar usando servicio
        try:
            RegistrationService.register_from_social_account(
                sociallogin,
                country=country,
                plan_type='trial',
                request=request
            )
        except Exception as e:
            # Log error pero no bloquear login
            import logging
            log = logging.getLogger(__name__)
            log.error(f"Error en registro social: {e}", exc_info=True)
```

## 🎨 Templates

### Botones de Registro Social

Agregar a `templates/account/signup.html`:

```html
{% load socialaccount %}

<!-- Botones de registro social -->
<div class="social-signup">
    <h3>O registrate con:</h3>
    
    <a href="{% provider_login_url 'google' %}" class="btn btn-google">
        🔵 Continuar con Google
    </a>
    
    <a href="{% provider_login_url 'microsoft' %}" class="btn btn-microsoft">
        ⚪ Continuar con Microsoft
    </a>
</div>
```

## ✅ Ventajas del Registro Social

1. **Menos Fricción**
   - Un clic y listo
   - No recordar contraseñas

2. **Mayor Seguridad**
   - Autenticación de terceros confiables
   - Email verificado automáticamente

3. **Mejor para B2B**
   - Microsoft es popular en empresas
   - Usa credenciales corporativas existentes

## 🚀 Próximos Pasos

1. **Configurar Credenciales**
   - Obtener Client ID y Secret de Google
   - Obtener Client ID y Secret de Microsoft
   - Configurar en settings o variables de entorno

2. **Probar Flujo**
   - Probar registro con Google
   - Probar registro con Microsoft
   - Verificar creación de empresa automática

3. **Personalizar**
   - Personalizar mensajes de bienvenida
   - Ajustar scopes según necesidades

## 📝 Notas

- **Email Verificado**: Los emails de Google/Microsoft ya están verificados, por lo que `skip_email_verification=True` es seguro.
- **Roles**: Por defecto se asigna rol 'Owner', pero puedes ajustarlo según necesites.
- **País**: Se detecta automáticamente desde `request.country` o usa 'CL' por defecto.

## 🎉 Resultado

Con esta configuración:
- ✅ Registro con Google disponible
- ✅ Registro con Microsoft disponible
- ✅ Creación automática de empresa
- ✅ Email verificado automáticamente

**¡Registro social listo para configurar!** 🚀

