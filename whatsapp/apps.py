from django.apps import AppConfig


class WhatsAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "whatsapp"
    label = "whatsapp"  # Asegurar que el label sea explícito
    verbose_name = "eGarage Air (WhatsApp)"

    def ready(self):
        """Importar señales y admin, y hacer warm-up del modelo OCR si está disponible"""
        # Importar admin para que se registre
        try:
            import whatsapp.admin

            # Llamar a la función de registro explícitamente
            if hasattr(whatsapp.admin, "register_whatsapp_admin"):
                whatsapp.admin.register_whatsapp_admin()
        except Exception as e:
            # Capturar cualquier error silenciosamente para no romper el admin
            # Solo loggear en DEBUG para no llenar logs en producción
            import logging

            logger = logging.getLogger(__name__)
            # Solo loggear si estamos en modo debug para no saturar logs en producción
            import django.conf

            if django.conf.settings.DEBUG:
                logger.warning(f"No se pudo importar/registrar whatsapp.admin: {e}")
            # No re-lanzar la excepción para que Django pueda seguir funcionando

        # OCR deshabilitado: warm-up omitido (easyocr/opencv no instalados)

        # import whatsapp.signals  # noqa
