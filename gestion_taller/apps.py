"""
AppConfig para gestion_taller que aplica el parche SSL de PostgreSQL
"""
from django.apps import AppConfig


class GestionTallerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "gestion_taller"

    def ready(self):
        """Aplicar parche SSL cuando la app esté lista"""
        # Aplicar el parche SSL para PostgreSQL localhost
        # Esto se ejecuta cuando Django inicia, antes de cualquier conexión
        try:
            from gestion_taller.db_patch import patch_postgresql_backend
            
            # Verificar si estamos usando PostgreSQL localhost
            from django.conf import settings
            db_config = settings.DATABASES.get("default", {})
            
            if db_config.get("ENGINE") == "django.db.backends.postgresql":
                db_host = db_config.get("HOST", "")
                # Aplicar el parche SIEMPRE para PostgreSQL localhost
                # No importa si el host está vacío o es localhost/127.0.0.1
                if db_host in ("127.0.0.1", "localhost", "::1") or not db_host or db_host == "":
                    # Aplicar el parche
                    patch_applied = patch_postgresql_backend()
                    if patch_applied:
                        import logging
                        logger = logging.getLogger(__name__)
                        if settings.DEBUG:
                            logger.info("✅ Parche SSL aplicado desde AppConfig para conexiones locales")
                    else:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning("⚠️ No se pudo aplicar parche SSL desde AppConfig")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"⚠️ No se pudo aplicar parche SSL desde AppConfig: {e}")
