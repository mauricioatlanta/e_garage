from allauth.account.adapter import DefaultAccountAdapter
from django.shortcuts import resolve_url

class EgarageAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        user = request.user
        
        # País por defecto según sesión, empresa o cookie
        pais = "cl"
        if hasattr(request, "session"):
            pais = request.session.get("modo_soporte_pais") or request.session.get("support_country") or "cl"
        
        lang = getattr(request, "LANGUAGE_CODE", "es") or "es"
        
        # Si es superusuario o staff
        if user.is_superuser:
            return f"/{pais}/{lang}/workspace/"
        
        # Si tiene empresa asignada
        if hasattr(user, "perfilusuario") and user.perfilusuario.empresa:
            emp_pais = (user.perfilusuario.empresa.pais or "cl").lower()
            return f"/{emp_pais}/{lang}/workspace/"
            
        return f"/{pais}/{lang}/workspace/"
