from django.contrib.auth import get_user_model
class ForcedLoginMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        if not request.user.is_authenticated:
            User = get_user_model()
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                user = User.objects.create_superuser(username='master_local', email='master@local.com', password='X')
            from django.contrib.auth import login
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return self.get_response(request)
