import hashlib

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from .empresa import Empresa


class SesionUsuario(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sesiones_trust")
    empresa = models.ForeignKey(
        Empresa, on_delete=models.CASCADE, null=True, blank=True, related_name="sesiones_trust"
    )
    session_key = models.CharField(max_length=40, unique=True)
    device_fingerprint = models.CharField(max_length=64, db_index=True)
    ip = models.GenericIPAddressField()
    pais = models.CharField(max_length=2, blank=True)
    user_agent = models.TextField(blank=True)
    navegador = models.CharField(max_length=120, blank=True)
    os = models.CharField(max_length=80, blank=True)
    es_mobile = models.BooleanField(default=False)
    inicio_sesion = models.DateTimeField(default=timezone.now)
    ultima_actividad = models.DateTimeField(default=timezone.now)
    paginas_visitadas = models.PositiveIntegerField(default=0)
    activa = models.BooleanField(default=True, db_index=True)
    flags = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Sesión de Usuario"
        verbose_name_plural = "Sesiones de Usuario"
        ordering = ["-ultima_actividad"]
        indexes = [
            models.Index(fields=["usuario", "activa"]),
            models.Index(fields=["empresa", "activa"]),
            models.Index(fields=["ultima_actividad"]),
        ]

    def __str__(self):
        return f"{self.usuario.username} | {self.ip} | {self.inicio_sesion:%Y-%m-%d %H:%M}"

    @staticmethod
    def build_fingerprint(user_agent: str, accept_language: str, accept_encoding: str) -> str:
        # Phase 1: server-side only (no JS). Intentionally lightweight — browser updates
        # or proxies can produce distinct fingerprints for the same physical device.
        # Phase 2+ will add canvas/font entropy via JS to increase stability.
        raw = f"{user_agent}|{accept_language}|{accept_encoding}"
        return hashlib.sha256(raw.encode("utf-8", errors="replace")).hexdigest()[:64]

    @staticmethod
    def parse_ua(user_agent: str) -> dict:
        """Minimal server-side UA parsing without external library."""
        ua = user_agent.lower()
        navegador = "Desconocido"
        os_name = "Desconocido"
        es_mobile = any(token in ua for token in ("mobile", "android", "iphone", "ipad"))

        for name, token in (
            ("Chrome", "chrome"),
            ("Firefox", "firefox"),
            ("Safari", "safari"),
            ("Edge", "edg"),
            ("Opera", "opr"),
            ("IE", "msie"),
            ("IE", "trident"),
        ):
            if token in ua:
                navegador = name
                break

        for name, token in (
            ("Windows", "windows"),
            ("macOS", "mac os"),
            ("iOS", "iphone"),
            ("iOS", "ipad"),
            ("Android", "android"),
            ("Linux", "linux"),
        ):
            if token in ua:
                os_name = name
                break

        return {"navegador": navegador, "os": os_name, "es_mobile": es_mobile}
