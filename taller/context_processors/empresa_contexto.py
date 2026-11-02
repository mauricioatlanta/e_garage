"""
Context processor para exponer datos de Empresa en todas las plantillas.
"""

from taller.services.empresa_service import get_empresa_safe


def empresa_contexto(request):
    """
    Context processor que expone la empresa del usuario autenticado.

    Si el usuario no está autenticado o no tiene empresa, devuelve None.
    Captura cualquier excepción para evitar Error 500.
    """
    user = getattr(request, "user", None)
    if not getattr(user, "is_authenticated", False):
        return {"empresa": None}

    try:
        empresa = get_empresa_safe(request)
        if empresa is None:
            return {
                "empresa": None,
                "nombre_taller": None,
            }
        return {
            "empresa": empresa,
            "nombre_taller": getattr(empresa, "nombre_taller", "eGarage"),
        }
    except Exception:
        # Si la columna no existe o hay cualquier error de DB,
        # devolvemos None para que el sitio no colapse.
        return {
            "empresa": None,
            "nombre_taller": None,
        }
