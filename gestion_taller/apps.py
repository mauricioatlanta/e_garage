from django.apps import AppConfig


class GestionTallerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "gestion_taller"

    def ready(self):
        # SSL monkey patch desactivado permanentemente.
        # Producción usa PostgreSQL correctamente vía settings_prod.py
        pass
