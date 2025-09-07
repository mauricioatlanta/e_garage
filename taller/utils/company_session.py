"""
Utilidades para manejo de empresa activa en sesión.
"""

from taller.models import Empresa


def set_active_company(request, empresa=None):
    """
    Establece la empresa activa en la sesión.
    Si no se proporciona empresa, usa la del usuario autenticado.
    """
    if not empresa and request.user.is_authenticated:
        try:
            empresa = Empresa.objects.get(user=request.user)
        except Empresa.DoesNotExist:
            empresa = None

    if empresa:
        request.session["empresa_id"] = empresa.id
        print(
            f"✅ Empresa activa establecida: {empresa.nombre_taller} (ID: {empresa.id})"
        )
    else:
        request.session.pop("empresa_id", None)
        print("⚠️  No se pudo establecer empresa activa")


def post_login_set_company(request):
    """
    Función para llamar después del login para establecer empresa por defecto.
    """
    set_active_company(request)
