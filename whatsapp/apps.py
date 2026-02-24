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
        
        # Warm-up del modelo OCR (evita demora del primer usuario)
        # Solo se ejecuta una vez al iniciar Django, en background para no bloquear
        try:
            import threading
            import logging
            
            logger = logging.getLogger(__name__)
            
            def warm_up_ocr():
                """Cargar modelo OCR en background para evitar demora del primer usuario"""
                try:
                    from whatsapp.services.ocr import get_reader
                    logger.info("Iniciando warm-up del modelo OCR en background...")
                    reader = get_reader(['es', 'en'], gpu=False)
                    if reader:
                        logger.info("Warm-up del modelo OCR completado exitosamente")
                    else:
                        logger.warning("EasyOCR no está disponible - warm-up omitido")
                except Exception as e:
                    # No bloquear inicio de Django si hay error
                    logger.debug(f"Error en warm-up de OCR (no crítico): {e}")
            
            # Ejecutar warm-up en thread separado para no bloquear inicio de Django
            threading.Thread(target=warm_up_ocr, daemon=True).start()
        except Exception as e:
            # Si hay error en el warm-up, no es crítico - solo loggear
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"No se pudo iniciar warm-up de OCR: {e}")
        
        # import whatsapp.signals  # noqa
