from pathlib import Path

from django.conf import settings
from django.core.files.storage import FileSystemStorage


class PrivateEvidenceStorage(FileSystemStorage):
    """Storage outside MEDIA_ROOT; files are served only by the auth view."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("location", Path(settings.BASE_DIR) / "private_media")
        super().__init__(*args, **kwargs)
        self.base_url = None

    def url(self, name):
        raise ValueError("Las evidencias de grúas no tienen URL pública")
