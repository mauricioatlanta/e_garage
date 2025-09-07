from django.conf import settings
from django.contrib.auth.decorators import login_required

# Fallback por si LOGIN_URL no está seteado
LOGIN_URL = getattr(settings, "LOGIN_URL", "/accounts/login/")
login_required_default = login_required(login_url=LOGIN_URL)
