#!/bin/bash
# Script para crear el archivo memoria_seguimiento.py en el servidor
# Ejecutar: sudo bash crear_memoria_seguimiento_servidor.sh

APP_DIR="/srv/egarage"
TARGET_FILE="$APP_DIR/taller/models/memoria_seguimiento.py"

echo "Creando archivo $TARGET_FILE..."

# Crear el archivo con el contenido completo
cat > "$TARGET_FILE" << 'PYTHON_EOF'
"""
Modelos para Memoria Interna + Evidencias + Seguimiento Público

Permite:
- Notas internas y etiquetas en documentos/clientes/vehículos
- Evidencias (fotos/videos) en documentos
- Seguimiento público con token para clientes
"""

import secrets

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from taller.models.mixins import AuditMixin


class NotaInterna(AuditMixin, models.Model):
    """
    Nota interna asociada a un documento, cliente o vehículo.
    Solo visible para staff (Owner/Admin), no para técnicos.
    """

    empresa = models.ForeignKey(
        "taller.Empresa",
        on_delete=models.CASCADE,
        related_name="notas_internas",
        db_index=True,
    )
    # XOR: solo uno de estos debe estar set
    documento = models.ForeignKey(
        "taller.Documento",
        on_delete=models.CASCADE,
        related_name="notas_internas",
        null=True,
        blank=True,
        db_index=True,
    )
    cliente = models.ForeignKey(
        "taller.Cliente",
        on_delete=models.CASCADE,
        related_name="notas_internas",
        null=True,
        blank=True,
        db_index=True,
    )
    vehiculo = models.ForeignKey(
        "taller.Vehiculo",
        on_delete=models.CASCADE,
        related_name="notas_internas",
        null=True,
        blank=True,
        db_index=True,
    )
    contenido = models.TextField(help_text=_("Contenido de la nota interna"))
    TIPO_CHOICES = [
        ("ALERTA", _("Alerta")),  # Roja en UI
        ("PREFERENCIA", _("Preferencia")),  # Amarilla en UI
    ]
    tipo = models.CharField(
        max_length=12,
        choices=TIPO_CHOICES,
        default="PREFERENCIA",
        db_index=True,
        help_text=_("Tipo de nota: Alerta (roja) o Preferencia (amarilla)"),
    )
    solo_staff = models.BooleanField(
        default=True,
        help_text=_("Si es True, solo visible para staff (Owner/Admin), no para técnicos"),
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = _("Nota Interna")
        verbose_name_plural = _("Notas Internas")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["empresa", "documento", "-created_at"]),
            models.Index(fields=["empresa", "cliente", "-created_at"]),
            models.Index(fields=["empresa", "vehiculo", "-created_at"]),
        ]

    def clean(self):
        super().clean()
        # Validación XOR: solo uno de documento/cliente/vehiculo debe estar set
        count = sum([bool(self.documento_id), bool(self.cliente_id), bool(self.vehiculo_id)])
        if count != 1:
            raise ValidationError(
                _("Debe especificar exactamente uno de: documento, cliente o vehículo")
            )

        # Validación de consistencia de empresa
        if self.documento_id and self.documento.empresa_id != self.empresa_id:
            raise ValidationError(_("El documento debe pertenecer a la misma empresa de la nota"))
        if self.cliente_id and self.cliente.empresa_id != self.empresa_id:
            raise ValidationError(_("El cliente debe pertenecer a la misma empresa de la nota"))
        if self.vehiculo_id and self.vehiculo.empresa_id != self.empresa_id:
            raise ValidationError(_("El vehículo debe pertenecer a la misma empresa de la nota"))

    def __str__(self):
        target = self.documento or self.cliente or self.vehiculo
        return f"Nota #{self.id} - {target}"


class EtiquetaInterna(AuditMixin, models.Model):
    """
    Etiqueta reutilizable para categorizar documentos/clientes/vehículos.
    Puede ser solo_staff (visible solo para staff) o público (visible para todos).
    """

    empresa = models.ForeignKey(
        "taller.Empresa",
        on_delete=models.CASCADE,
        related_name="etiquetas_internas",
        db_index=True,
    )
    nombre = models.CharField(max_length=50, help_text=_("Nombre de la etiqueta"))
    color = models.CharField(
        max_length=7,
        default="#3B82F6",
        help_text=_("Color en formato hex (#RRGGBB)"),
    )
    solo_staff = models.BooleanField(
        default=False,
        help_text=_("Si es True, solo visible para staff (Owner/Admin)"),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Etiqueta Interna")
        verbose_name_plural = _("Etiquetas Internas")
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "nombre"],
                name="uq_etiqueta_interna_empresa_nombre",
            )
        ]
        indexes = [
            models.Index(fields=["empresa", "solo_staff"]),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.empresa.nombre_taller})"


class EtiquetaAsignacion(models.Model):
    """
    Asignación de etiquetas a documentos/clientes/vehículos.
    """

    empresa = models.ForeignKey(
        "taller.Empresa",
        on_delete=models.CASCADE,
        related_name="etiqueta_asignaciones",
        db_index=True,
    )
    etiqueta = models.ForeignKey(
        EtiquetaInterna,
        on_delete=models.CASCADE,
        related_name="asignaciones",
        db_index=True,
    )
    # XOR: solo uno de estos debe estar set
    documento = models.ForeignKey(
        "taller.Documento",
        on_delete=models.CASCADE,
        related_name="etiqueta_asignaciones",
        null=True,
        blank=True,
        db_index=True,
    )
    cliente = models.ForeignKey(
        "taller.Cliente",
        on_delete=models.CASCADE,
        related_name="etiqueta_asignaciones",
        null=True,
        blank=True,
        db_index=True,
    )
    vehiculo = models.ForeignKey(
        "taller.Vehiculo",
        on_delete=models.CASCADE,
        related_name="etiqueta_asignaciones",
        null=True,
        blank=True,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Asignación de Etiqueta")
        verbose_name_plural = _("Asignaciones de Etiquetas")
        constraints = [
            models.UniqueConstraint(
                fields=["etiqueta", "documento"],
                name="uq_etiqueta_asignacion_documento",
                condition=models.Q(documento__isnull=False),
            ),
            models.UniqueConstraint(
                fields=["etiqueta", "cliente"],
                name="uq_etiqueta_asignacion_cliente",
                condition=models.Q(cliente__isnull=False),
            ),
            models.UniqueConstraint(
                fields=["etiqueta", "vehiculo"],
                name="uq_etiqueta_asignacion_vehiculo",
                condition=models.Q(vehiculo__isnull=False),
            ),
        ]
        indexes = [
            models.Index(fields=["empresa", "documento"]),
            models.Index(fields=["empresa", "cliente"]),
            models.Index(fields=["empresa", "vehiculo"]),
        ]

    def clean(self):
        super().clean()
        # Validación XOR
        count = sum([bool(self.documento_id), bool(self.cliente_id), bool(self.vehiculo_id)])
        if count != 1:
            raise ValidationError(
                _("Debe especificar exactamente uno de: documento, cliente o vehículo")
            )

        # Validación de consistencia de empresa
        if self.documento_id and self.documento.empresa_id != self.empresa_id:
            raise ValidationError(
                _("El documento debe pertenecer a la misma empresa de la asignación")
            )
        if self.cliente_id and self.cliente.empresa_id != self.empresa_id:
            raise ValidationError(
                _("El cliente debe pertenecer a la misma empresa de la asignación")
            )
        if self.vehiculo_id and self.vehiculo.empresa_id != self.empresa_id:
            raise ValidationError(
                _("El vehículo debe pertenecer a la misma empresa de la asignación")
            )
        if self.etiqueta.empresa_id != self.empresa_id:
            raise ValidationError(
                _("La etiqueta debe pertenecer a la misma empresa de la asignación")
            )

    def __str__(self):
        target = self.documento or self.cliente or self.vehiculo
        return f"{self.etiqueta.nombre} → {target}"


class EvidenciaDocumento(AuditMixin, models.Model):
    """
    Evidencia (foto/video) asociada a un documento.
    Límites: 4 fotos + 1 video por documento.
    """

    TIPO_CHOICES = [
        ("FOTO", _("Foto")),
        ("VIDEO", _("Video")),
    ]

    empresa = models.ForeignKey(
        "taller.Empresa",
        on_delete=models.CASCADE,
        related_name="evidencias_documento",
        db_index=True,
    )
    documento = models.ForeignKey(
        "taller.Documento",
        on_delete=models.CASCADE,
        related_name="evidencias",
        db_index=True,
    )
    tipo = models.CharField(max_length=5, choices=TIPO_CHOICES, db_index=True)
    archivo = models.FileField(
        upload_to="evidencias_documentos/%Y/%m/",
        help_text=_("Archivo de foto o video"),
    )
    descripcion = models.TextField(blank=True, null=True, help_text=_("Descripción opcional"))
    compartible = models.BooleanField(
        default=False,
        help_text=_("Si es True, se muestra en el seguimiento público"),
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = _("Evidencia de Documento")
        verbose_name_plural = _("Evidencias de Documentos")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["empresa", "documento", "tipo", "-created_at"]),
            models.Index(fields=["documento", "compartible"]),
        ]

    def clean(self):
        super().clean()
        # Validación de consistencia de empresa
        if self.documento.empresa_id != self.empresa_id:
            raise ValidationError(
                _("El documento debe pertenecer a la misma empresa de la evidencia")
            )

        # Validación de límites: 4 fotos + 1 video
        # Excluirse a sí mismo en updates
        qs_existentes = EvidenciaDocumento.objects.filter(documento=self.documento)
        if self.pk:
            qs_existentes = qs_existentes.exclude(pk=self.pk)

        fotos_existentes = qs_existentes.filter(tipo="FOTO").count()
        videos_existentes = qs_existentes.filter(tipo="VIDEO").count()

        if self.tipo == "FOTO" and fotos_existentes >= 4:
            raise ValidationError(_("Máximo 4 fotos por documento"))
        if self.tipo == "VIDEO" and videos_existentes >= 1:
            raise ValidationError(_("Máximo 1 video por documento"))

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.documento.numero_documento}"


class SeguimientoPublico(models.Model):
    """
    Seguimiento público de un documento con token único.
    Permite a clientes ver estado y evidencias compartibles sin login.
    """

    empresa = models.ForeignKey(
        "taller.Empresa",
        on_delete=models.CASCADE,
        related_name="seguimientos_publicos",
        db_index=True,
    )
    documento = models.OneToOneField(
        "taller.Documento",
        on_delete=models.CASCADE,
        related_name="seguimiento_publico",
        db_index=True,
    )
    token = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text=_("Token único para acceso público"),
    )
    activo = models.BooleanField(
        default=True,
        help_text=_("Si es False, el link de seguimiento no funciona"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Seguimiento Público")
        verbose_name_plural = _("Seguimientos Públicos")
        indexes = [
            models.Index(fields=["token", "activo"]),
            models.Index(fields=["empresa", "documento"]),
        ]

    def clean(self):
        super().clean()
        # Validación de consistencia de empresa
        if self.documento.empresa_id != self.empresa_id:
            raise ValidationError(
                _("El documento debe pertenecer a la misma empresa del seguimiento")
            )

    def save(self, *args, **kwargs):
        if not self.token:
            # Generar token único
            self.token = secrets.token_urlsafe(32)
        self.full_clean()
        super().save(*args, **kwargs)

    def get_url_absoluta(self, request):
        """Obtiene la URL absoluta del seguimiento público"""
        from django.urls import reverse

        return request.build_absolute_uri(
            reverse("documentos:seguimiento_publico", args=[self.token])
        )

    def __str__(self):
        return f"Seguimiento {self.documento.numero_documento} - {self.token[:8]}..."
PYTHON_EOF

# Ajustar permisos
APP_USER=$(stat -c '%U' "$APP_DIR")
APP_GROUP=$(stat -c '%G' "$APP_DIR")
chown "$APP_USER:$APP_GROUP" "$TARGET_FILE"
chmod 644 "$TARGET_FILE"

echo "✅ Archivo creado: $TARGET_FILE"
echo "✅ Permisos ajustados: $APP_USER:$APP_GROUP"
echo ""
echo "Ahora reinicia el servicio:"
echo "  sudo systemctl restart egarage-gunicorn.service"
