from django import template

register = template.Library()

# Diccionario de traducciones
TRANSLATIONS = {
    'en': {
        'Iniciar sesion': 'Sign In',
        'Email': 'Email',
        'E-mail': 'Email',
        'Contrasena': 'Password',
        'Password': 'Password',
        'Recordarme': 'Remember me',
        'Remember Me': 'Remember me',
        'Olvidaste tu contrasena?': 'Forgot your password?',
        'No tienes cuenta?': "Don't have an account?",
        'Registrate aqui': 'Sign up here',
        'ACCESO RESTRINGIDO': 'ACCESS RESTRICTED',
        'Esta cuenta ya tiene un usuario asignado.': 'This account already has a user assigned.',
        'No es posible registrar otro usuario para esta suscripcion.': 'It is not possible to register another user for this subscription.',
        'Cada taller/empresa puede tener unicamente': 'Each workshop/company can only have',
        'UN USUARIO ACTIVO': 'ONE ACTIVE USER',
        'Si necesitas cambiar el usuario principal, contacta al administrador del sistema.': 'If you need to change the main user, contact the system administrator.',
        'Volver al Registro': 'Back to Registration'
    }
}

@register.simple_tag(takes_context=True)
def trans(context, text):
    """
    Template tag personalizado para traducciones
    """
    request = context.get('request')
    if not request:
        return text
    
    # Obtener idioma de la sesión o parámetro URL
    lang = request.GET.get('lang') or request.session.get('language', 'es')
    
    # Si es español o no hay traducción, devolver texto original
    if lang == 'es' or lang not in TRANSLATIONS:
        return text
    
    # Devolver traducción si existe
    return TRANSLATIONS[lang].get(text, text)

@register.simple_tag(takes_context=True)
def precio_pais(context, precio):
    """
    Formatea el precio según el país del usuario
    """
    request = context.get('request')
    if not request or not hasattr(request, 'user') or not hasattr(request.user, 'empresa'):
        return f"${precio:,.0f}"
    
    empresa = request.user.empresa
    
    if empresa.pais == 'US':
        return f"${precio:,.2f} USD"
    else:
        return f"${precio:,.0f} CLP"

@register.simple_tag(takes_context=True)
def simbolo_moneda(context):
    """
    Retorna el símbolo de moneda según el país del usuario
    """
    request = context.get('request')
    if not request or not hasattr(request, 'user') or not hasattr(request.user, 'empresa'):
        return "$"
    
    return request.user.empresa.simbolo_moneda

@register.filter
def es_usa(user):
    """
    Verifica si el usuario es de USA
    """
    return hasattr(user, 'empresa') and user.empresa.pais == 'US'

@register.filter  
def es_chile(user):
    """
    Verifica si el usuario es de Chile
    """
    return hasattr(user, 'empresa') and user.empresa.pais == 'CL'
