import os
import sys

from django.contrib.auth import get_user_model
from django.core.management import setup_environ

# Ajustar el path para importar settings
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from e_garage import settings

    setup_environ(settings)
except ImportError:
    pass

User = get_user_model()

print("\nUSUARIOS REGISTRADOS EN E-GARAGE\n")
print(
    "{:<15} {:<30} {:<10} {:<10} {:<10}".format(
        "Username", "Email", "Activo", "Staff", "Superuser"
    )
)
print("-" * 80)
for user in User.objects.all():
    print(
        f"{user.username:<15} {user.email:<30} {str(user.is_active):<10} {str(user.is_staff):<10} {str(user.is_superuser):<10}"
    )
print("\nPuedes resetear contraseñas con: python manage.py changepassword <username>\n")
