from django.contrib.auth import get_user_model

User = get_user_model()

if not User.objects.filter(username="testuser_usa").exists():
    User.objects.create_user(
        username="testuser_usa",
        email="testuser@usa-garage.com",
        password="TestUSA2025!",
        is_active=True,
    )
    print("Usuario testuser_usa creado.")
else:
    print("El usuario testuser_usa ya existe.")
