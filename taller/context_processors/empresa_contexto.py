"""
Context processor para exponer datos de Empresa en todas las plantillas.
"""
from taller.models.empresa import Empresa


def empresa_contexto(request):
    """
    Context processor que expone la empresa del usuario autenticado.
    
    Si el usuario no está autenticado o no tiene empresa, devuelve None.
    Captura cualquier excepción para evitar Error 500.
    """
    if not request.user.is_authenticated:
        return {'empresa': None}
    
    try:
        # Intentamos obtener la empresa vinculada al usuario
        empresa = Empresa.objects.get(user=request.user)
        return {
            'empresa': empresa,
            'nombre_taller': getattr(empresa, "nombre_taller", "eGarage"),
        }
    except Exception:
        # Si la columna no existe o hay cualquier error de DB, 
        # devolvemos None para que el sitio no colapse.
        return {
            'empresa': None,
            'nombre_taller': None,
        }
