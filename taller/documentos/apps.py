from django.apps import AppConfig


class DocumentosConfig(AppConfig):
    name = "taller.documentos"

    def ready(self):
        from . import signals  # noqa
