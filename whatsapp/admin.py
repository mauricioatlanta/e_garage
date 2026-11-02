"""
Admin para eGarage Air - WhatsApp v2 Final
"""

from django.contrib import admin
from django.apps import apps

# Verificar que la app esté disponible antes de registrar
try:
    from .models import EmpresaWhatsAppConfig, WhatsAppSession

    class EmpresaWhatsAppConfigAdmin(admin.ModelAdmin):
        # Añadimos los campos de habilitación para ver rápido el estado del servicio
        list_display = (
            "empresa",
            "phone_number_id",
            "allowed_operator_phone",
            "is_enabled",
            "enable_audio",
            "enable_ocr",
        )
        list_filter = ("is_enabled", "enable_audio", "enable_ocr")
        search_fields = ("empresa__nombre_taller", "allowed_operator_phone", "phone_number_id")
        raw_id_fields = ("empresa",)
        # Agrupamos por secciones para que sea más profesional
        fieldsets = (
            (
                "Identificación",
                {"fields": ("empresa", "phone_number_id", "allowed_operator_phone")},
            ),
            ("Estado y Funciones", {"fields": ("is_enabled", "enable_audio", "enable_ocr")}),
        )

    class WhatsAppSessionAdmin(admin.ModelAdmin):
        # list_display con created_at e is_expired para monitoreo en tiempo real
        list_display = (
            "operator_phone",
            "empresa",
            "estado",
            "created_at",
            "last_interaction",
            "is_expired",
        )
        list_filter = ("estado", "empresa", "last_interaction")
        search_fields = ("operator_phone", "empresa__nombre_taller")
        raw_id_fields = ("empresa",)
        # Solo campos que no deben editarse manualmente
        readonly_fields = ("created_at", "last_interaction", "contexto")

        @admin.display(
            description="Sesión Expirada",
            boolean=True,
        )
        def is_expired(self, obj):
            """Verificar si la sesión ha expirado con manejo de errores"""
            try:
                return obj.is_expired()
            except Exception:
                return False

    # Registrar solo si la app está cargada
    def register_whatsapp_admin():
        """Registrar los modelos solo si la app está cargada"""
        try:
            apps.get_app_config("whatsapp")
            # Solo registrar si no están ya registrados
            if not admin.site.is_registered(EmpresaWhatsAppConfig):
                admin.site.register(EmpresaWhatsAppConfig, EmpresaWhatsAppConfigAdmin)
            if not admin.site.is_registered(WhatsAppSession):
                admin.site.register(WhatsAppSession, WhatsAppSessionAdmin)
        except (LookupError, AttributeError, ImportError) as e:
            # La app no está cargada o hay problemas, no registrar
            import logging

            logger = logging.getLogger(__name__)
            # Solo loggear en modo DEBUG para no saturar logs en producción
            import django.conf

            if django.conf.settings.DEBUG:
                logger.warning(f"App 'whatsapp' no está disponible: {e}")
        except Exception as e:
            # Capturar cualquier otro error inesperado para no romper el admin
            import logging

            logger = logging.getLogger(__name__)
            # Solo loggear en modo DEBUG
            import django.conf

            if django.conf.settings.DEBUG:
                logger.error(f"Error inesperado al registrar admin de WhatsApp: {e}", exc_info=True)

    # No registrar automáticamente aquí, se hará en apps.py ready()

except ImportError as e:
    # Los modelos no se pueden importar (esperado si la app no está desplegada en este servidor)
    import logging

    logger = logging.getLogger(__name__)
    import django.conf

    if django.conf.settings.DEBUG:
        logger.debug("WhatsApp admin no registrado (modelos no disponibles): %s", e)

    # Función dummy para evitar errores
    def register_whatsapp_admin():
        pass

except Exception as e:
    # Capturar cualquier otro error inesperado al importar
    import logging

    logger = logging.getLogger(__name__)
    import django.conf

    if django.conf.settings.DEBUG:
        logger.error(f"Error inesperado en whatsapp/admin.py: {e}", exc_info=True)

    # Función dummy para evitar errores
    def register_whatsapp_admin():
        pass
