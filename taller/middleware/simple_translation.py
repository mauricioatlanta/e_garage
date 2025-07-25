class SimpleTranslationMiddleware:
    """
    Middleware simple para traducciones sin usar archivos .mo
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Diccionario de traducciones
        self.translations = {
            'en': {
                'Iniciar sesion': 'Sign In',
                'Email': 'Email',
                'Contrasena': 'Password', 
                'Recordarme': 'Remember me',
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
    
    def __call__(self, request):
        # Obtener el idioma de la URL
        lang = request.GET.get('lang', 'es')
        
        # Guardar el idioma en la sesión
        if lang in ['en', 'es']:
            request.session['language'] = lang
            request.current_language = lang
        else:
            request.current_language = request.session.get('language', 'es')
        
        response = self.get_response(request)
        return response