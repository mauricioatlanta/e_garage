"""
EmpresaDominio — dominio personalizado de un tenant.

Ciclo de vida de estados:
    PENDIENTE → VERIFICANDO → ACTIVO
                            → ERROR_DNS
    ACTIVO    → SUSPENDIDO  (acción administrativa)
    ACTIVO    → SSL_PENDIENTE → ACTIVO (con ssl_emitido=True)

Restricciones de integridad:
    - Un dominio solo puede pertenecer a una empresa (unique en dominio).
    - Solo puede existir un dominio ACTIVO por empresa a la vez.

Fase 1: solo el modelo y sus validaciones.
Fase 2: HostTenantMiddleware + verificación DNS.
Fase 3: emisión SSL automática.
"""

import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


# Dominios reservados que un tenant jamás puede registrar como propios.
DOMINIOS_RESERVADOS = frozenset(
    [
        "egarage.cl",
        "www.egarage.cl",
        "proxy.egarage.cl",
        "api.egarage.cl",
        "app.egarage.cl",
        "mail.egarage.cl",
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
    ]
)


class EmpresaDominio(models.Model):
    """Dominio personalizado asociado a un tenant de eGarage."""

    class Estado(models.TextChoices):
        PENDIENTE     = "PENDIENTE",     "Pendiente de verificación"
        VERIFICANDO   = "VERIFICANDO",   "Verificación en curso"
        ACTIVO        = "ACTIVO",        "Activo"
        ERROR_DNS     = "ERROR_DNS",     "Error en verificación DNS"
        SSL_PENDIENTE = "SSL_PENDIENTE", "SSL en trámite"
        SUSPENDIDO    = "SUSPENDIDO",    "Suspendido"

    # ── Relación ──────────────────────────────────────────────────────────
    empresa = models.ForeignKey(
        "taller.Empresa",
        on_delete=models.CASCADE,
        related_name="dominios_personalizados",
    )

    # ── Dominio ───────────────────────────────────────────────────────────
    dominio = models.CharField(
        max_length=253,  # RFC 1035: longitud máxima de un FQDN
        unique=True,
        db_index=True,
        help_text="FQDN sin protocolo ni barra final. Ej: taller.midominio.cl",
    )
    estado = models.CharField(
        max_length=15,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
        db_index=True,
    )

    # ── Verificación DNS ──────────────────────────────────────────────────
    token_verificacion = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        help_text="Token para el registro TXT. No rota una vez creado.",
    )
    verificado_en           = models.DateTimeField(null=True, blank=True)
    ultimo_check_dns        = models.DateTimeField(null=True, blank=True)
    intentos_verificacion   = models.PositiveSmallIntegerField(default=0)

    # ── SSL ───────────────────────────────────────────────────────────────
    ssl_emitido   = models.BooleanField(default=False)
    ssl_cert_path = models.CharField(max_length=512, blank=True, default="")
    ssl_key_path  = models.CharField(max_length=512, blank=True, default="")
    ssl_expira_en = models.DateField(null=True, blank=True)

    # ── DNS ───────────────────────────────────────────────────────────────
    incluir_www = models.BooleanField(
        default=True,
        help_text=(
            "Si está activo, la emisión SSL y la configuración Nginx incluyen "
            "también www.<dominio> como alias (SAN adicional en el mismo "
            "certificado). Desactivar solo si el tenant no puede o no quiere "
            "configurar el CNAME de www."
        ),
    )

    # ── Auditoría ─────────────────────────────────────────────────────────
    creado_en      = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    creado_por     = models.ForeignKey(
        "auth.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        verbose_name        = "Dominio personalizado"
        verbose_name_plural = "Dominios personalizados"
        indexes = [
            # Lookup crítico de HostTenantMiddleware: O(log n), cubierto por índice compuesto.
            models.Index(fields=["dominio", "estado"], name="idx_empdominio_dominio_estado"),
            # Lookup por empresa (admin, panel de configuración).
            models.Index(fields=["empresa", "estado"], name="idx_empdominio_empresa_estado"),
        ]
        constraints = [
            # Solo un dominio ACTIVO por empresa.
            models.UniqueConstraint(
                fields=["empresa"],
                condition=models.Q(estado="ACTIVO"),
                name="uq_empresa_dominio_activo",
            ),
        ]

    # ── Propiedades ───────────────────────────────────────────────────────

    @property
    def esta_activo(self) -> bool:
        return self.estado == self.Estado.ACTIVO

    @property
    def esta_verificado(self) -> bool:
        return self.estado in (self.Estado.ACTIVO, self.Estado.SSL_PENDIENTE)

    @property
    def puede_verificarse(self) -> bool:
        return self.estado in (self.Estado.PENDIENTE, self.Estado.VERIFICANDO, self.Estado.ERROR_DNS)

    # ── Métodos de verificación DNS ───────────────────────────────────────

    def get_txt_record_name(self) -> str:
        """Nombre del registro TXT que el tenant debe crear en su DNS."""
        return f"_egarage-verify.{self.dominio}"

    def get_txt_record_value(self) -> str:
        """Valor del registro TXT que el tenant debe crear en su DNS."""
        return f"egarage-verify={self.token_verificacion}"

    def get_cname_target(self) -> str:
        """Deprecated compatibility helper.

        Antes de ADR-004 devolvía "proxy.egarage.cl", un target que nunca
        existió en DNS (ver auditoría Fase 340-342). La arquitectura real
        (confirmada por el único tenant ya operando, MonteAzul) es apex A
        directo al VPS + www como CNAME AL APEX, no a un proxy intermedio.

        Se mantiene por compatibilidad con callers existentes (admin, tests
        históricos) — devuelve el destino real del CNAME opcional de "www":
        el propio dominio apex.
        """
        return self.dominio

    def get_dns_instructions(self) -> dict:
        """Instrucciones DNS estructuradas (ADR-004: arquitectura A_DIRECT_VPS).

        Devuelve un dict con los registros que el tenant debe crear:
            - apex: A -> IP del VPS (settings.CUSTOM_DOMAIN_VPS_IP)
            - www:  CNAME -> dominio apex (solo si incluir_www)
            - txt:  registro de verificación

        No incluye HTML ni texto — la presentación vive en el template/admin.
        """
        from django.conf import settings

        return {
            "apex": {
                "type": "A",
                "name": "@",
                "value": settings.CUSTOM_DOMAIN_VPS_IP,
            },
            "www": {
                "enabled": self.incluir_www,
                "type": "CNAME",
                "name": "www",
                "value": self.dominio,
            },
            "txt": {
                "type": "TXT",
                "name": self.get_txt_record_name(),
                "value": self.get_txt_record_value(),
            },
        }

    # ── Transiciones de estado ────────────────────────────────────────────

    def marcar_verificado(self) -> None:
        """Transicionar a ACTIVO tras verificación TXT exitosa."""
        self.estado       = self.Estado.ACTIVO
        self.verificado_en = timezone.now()
        self.save(update_fields=["estado", "verificado_en", "actualizado_en"])

    def suspender(self, *, motivo: str = "") -> None:
        """Suspender el dominio (acción administrativa)."""
        self.estado = self.Estado.SUSPENDIDO
        self.save(update_fields=["estado", "actualizado_en"])

    def iniciar_verificacion(self) -> None:
        """Transicionar a VERIFICANDO cuando se lanza el proceso de check DNS."""
        if not self.puede_verificarse:
            raise ValueError(
                f"No se puede iniciar verificación desde estado '{self.estado}'."
            )
        self.estado = self.Estado.VERIFICANDO
        self.save(update_fields=["estado", "actualizado_en"])

    # ── Validación ────────────────────────────────────────────────────────

    def clean(self) -> None:
        super().clean()
        self._validar_formato_dominio()
        self._validar_no_reservado()

    def _validar_formato_dominio(self) -> None:
        dominio = (self.dominio or "").strip().lower()
        if not dominio:
            raise ValidationError({"dominio": "El dominio no puede estar vacío."})
        if dominio != self.dominio:
            raise ValidationError(
                {"dominio": "El dominio debe estar en minúsculas y sin espacios."}
            )
        if "://" in dominio:
            raise ValidationError(
                {"dominio": "El dominio no debe incluir protocolo (http:// / https://)."}
            )
        if dominio.endswith("/"):
            raise ValidationError(
                {"dominio": "El dominio no debe terminar con barra '/'."}
            )
        if " " in dominio:
            raise ValidationError({"dominio": "El dominio no puede contener espacios."})
        if len(dominio) > 253:
            raise ValidationError(
                {"dominio": "El dominio supera la longitud máxima (253 caracteres)."}
            )
        # Cada etiqueta DNS: max 63 chars, alfanumérico + guiones, no empieza/termina con guión
        partes = dominio.split(".")
        if len(partes) < 2:
            raise ValidationError(
                {"dominio": "El dominio debe tener al menos un punto (ej: taller.midominio.com)."}
            )
        for parte in partes:
            if not parte:
                raise ValidationError({"dominio": "El dominio contiene etiquetas vacías (doble punto)."})
            if len(parte) > 63:
                raise ValidationError(
                    {"dominio": f"La etiqueta '{parte}' supera 63 caracteres."}
                )
            if parte.startswith("-") or parte.endswith("-"):
                raise ValidationError(
                    {"dominio": f"La etiqueta '{parte}' no puede comenzar ni terminar con guión."}
                )
            if not all(c.isalnum() or c == "-" for c in parte):
                raise ValidationError(
                    {"dominio": f"La etiqueta '{parte}' contiene caracteres no permitidos."}
                )

    def _validar_no_reservado(self) -> None:
        dominio = (self.dominio or "").lower()
        if dominio in DOMINIOS_RESERVADOS:
            raise ValidationError(
                {"dominio": f"El dominio '{dominio}' está reservado y no puede ser registrado."}
            )
        # Bloquear también subdominios de egarage.cl
        if dominio.endswith(".egarage.cl"):
            raise ValidationError(
                {"dominio": "Los subdominios de egarage.cl están reservados."}
            )

    def save(self, *args, **kwargs) -> None:
        # Normalizar a minúsculas antes de guardar
        if self.dominio:
            self.dominio = self.dominio.strip().lower()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.dominio} → {self.empresa_id} [{self.estado}]"
