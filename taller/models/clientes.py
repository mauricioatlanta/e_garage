from django.contrib.auth.models import User
from django.db import models

from .color_cliente import ColorCliente
from .region_ciudad import TallerCiudad, TallerRegion
from .ubicacion import Ciudad as CiudadUSA
from .ubicacion import Estado as EstadoUSA


class AuditModelMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_%(class)s",
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_%(class)s",
    )

    class Meta:
        abstract = True


from django.db.models import Index, Q, UniqueConstraint

from core.models import TenantManager, TenantScoped


class Cliente(AuditModelMixin, TenantScoped):
    # empresa viene de TenantScoped (nullable en migración inicial)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100, blank=True, null=True)
    telefono = models.CharField(max_length=15, blank=True, null=True, db_index=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)

    # === CAMPOS LEGACY (DEPRECAR EN FUTURO) ===
    # Mantener para compatibilidad, migrar a Address progresivamente

    # Campos para Chile (legacy)
    region = models.ForeignKey(
        TallerRegion,
        models.DO_NOTHING,
        blank=True,
        null=True,
        help_text="[LEGACY] Usar billing_address en su lugar",
    )
    ciudad = models.ForeignKey(
        TallerCiudad,
        models.DO_NOTHING,
        blank=True,
        null=True,
        help_text="[LEGACY] Usar billing_address en su lugar",
    )

    # Campos para USA/BR/VE/PE (legacy - reutilizados para múltiples países)
    estado_usa = models.ForeignKey(
        EstadoUSA,
        models.DO_NOTHING,
        blank=True,
        null=True,
        help_text="[LEGACY] Estado para USA/Brasil/Venezuela/Perú - Usar billing_address",
    )
    ciudad_usa = models.ForeignKey(
        CiudadUSA,
        models.DO_NOTHING,
        blank=True,
        null=True,
        help_text="[LEGACY] Ciudad para USA/Brasil/Venezuela/Perú - Usar billing_address",
    )
    zipcode = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text="[LEGACY] Código postal - Usar billing_address.postal_code",
    )

    # === NUEVOS CAMPOS (ARQUITECTURA LIMPIA) ===
    # Direcciones estructuradas usando modelo Address unificado

    billing_address = models.ForeignKey(
        "ubicacion.Address",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="clients_billing",
        verbose_name="Dirección de Facturación",
        help_text="Dirección principal del cliente (facturación)",
    )
    shipping_address = models.ForeignKey(
        "ubicacion.Address",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="clients_shipping",
        verbose_name="Dirección de Envío",
        help_text="Dirección de envío/entrega (opcional, si difiere de facturación)",
    )

    email = models.EmailField(blank=True, null=True, db_index=True)

    # === IDENTIFICADOR TRIBUTARIO (multi-país) ===
    TAX_ID_TYPES = (
        ("CL_RUT", "RUT (Chile)"),
        ("US_EIN", "EIN (USA - Empresa)"),
        ("US_SSN", "SSN (USA - Persona)"),
        ("BR_CPF", "CPF (Brasil - Pessoa)"),
        ("BR_CNPJ", "CNPJ (Brasil - Empresa)"),
        ("PE_RUC", "RUC (Perú)"),
        ("VE_RIF", "RIF (Venezuela)"),
    )

    tax_id_type = models.CharField(
        max_length=12,
        choices=TAX_ID_TYPES,
        default="CL_RUT",
        verbose_name="Tipo de Identificador Tributario",
        help_text="Tipo de documento tributario según el país",
    )
    tax_id = models.CharField(
        max_length=32,
        blank=True,
        default="",
        db_index=True,
        verbose_name="Identificador Tributario",
        help_text="RUT/EIN/SSN/CPF/CNPJ/RUC/RIF según el tipo seleccionado",
    )

    # Campo para identificación por color
    color = models.ForeignKey(
        ColorCliente,
        models.SET_NULL,
        blank=True,
        null=True,
        help_text="Color para identificar al cliente/subscriptor",
    )

    objects = TenantManager()

    class Meta(TenantScoped.Meta):
        db_table = "taller_cliente"
        managed = True
        indexes = [
            Index(fields=["empresa", "apellido", "nombre"]),
            Index(fields=["empresa", "email"]),
            Index(fields=["empresa", "tax_id"]),
        ]
        constraints = [
            UniqueConstraint(
                fields=["empresa", "email"],
                condition=Q(email__isnull=False) & ~Q(email=""),
                name="uq_cliente_empresa_email_present",
            ),
            UniqueConstraint(
                fields=["empresa", "tax_id"],
                condition=Q(tax_id__isnull=False) & ~Q(tax_id=""),
                name="uq_cliente_empresa_taxid_present",
            ),
        ]

    def __str__(self):
        nombre = self.nombre or ""
        apellido = self.apellido or ""
        texto = (nombre + " " + apellido).strip()
        if texto:
            return texto
        if self.email:
            return f"{self.email}"
        if self.telefono:
            return f"Cliente {self.telefono}"
        return f"Cliente #{self.pk}"

    def get_absolute_url(self):
        # Devuelve la URL con el prefijo de país correcto
        if hasattr(self, "empresa") and self.empresa and hasattr(self.empresa, "pais"):
            pais = self.empresa.pais.lower()
            return f"/{pais}/dashboard/suscriptor/{self.pk}/"
        return f"/dashboard/suscriptor/{self.pk}/"

    def get_colores_disponibles(self):
        """Obtiene los colores disponibles según el país de la empresa"""
        if hasattr(self, "empresa") and self.empresa and hasattr(self.empresa, "pais"):
            return ColorCliente.get_colores_para_pais(self.empresa.pais)
        return ColorCliente.get_colores_para_pais("CL")  # Default Chile

    def get_color_display(self):
        """Retorna el color del cliente con su código hexadecimal"""
        if self.color:
            return {
                "nombre": self.color.nombre,
                "codigo": self.color.codigo_color,
                "css_class": self.color.get_css_class(),
                "style": self.color.get_style_attribute(),
            }
        return None

    def clean(self):
        """
        Validaciones de consistencia por país.

        Validaciones:
        1. Campos legacy según país
        2. Tax ID con validación y normalización completa
        3. Teléfono con formato válido (opcional)
        """
        from django.core.exceptions import ValidationError
        from taller.utils.validators import validar_tax_id, validar_telefono

        super().clean()

        # País de la empresa (siempre debería existir con TenantScoped)
        pais = getattr(getattr(self, "empresa", None), "pais", None)

        # Si no conocemos el país, no forzamos nada (pero lo ideal es que siempre exista)
        if not pais:
            return

        # === VALIDACIÓN DE CAMPOS LEGACY POR PAÍS ===

        # Reglas CL
        if pais == "CL":
            if self.estado_usa_id or self.ciudad_usa_id or self.zipcode:
                raise ValidationError("Para clientes de Chile no se deben completar campos de USA.")

        # Reglas US
        if pais == "US":
            if self.region_id or self.ciudad_id:
                raise ValidationError(
                    "Para clientes de USA no se deben completar región/ciudad de Chile."
                )

        # === VALIDACIÓN Y NORMALIZACIÓN DE TAX ID ===
        # ✅ IMPORTANTE: tax_id es dato sensible
        # ✅ Usar validadores específicos por tipo
        # ✅ Normalización automática

        if self.tax_id and self.tax_id_type:
            try:
                # ✅ Validar y normalizar usando validadores específicos
                self.tax_id = validar_tax_id(self.tax_id, self.tax_id_type)
            except ValidationError as e:
                # Re-raise con contexto del campo
                raise ValidationError({"tax_id": e.messages})

        # === VALIDACIÓN DE TELÉFONO (OPCIONAL) ===
        # ✅ Si libphonenumber está instalado, validar formato

        if self.telefono and pais:
            try:
                self.telefono = validar_telefono(self.telefono, pais)
            except ValidationError:
                # No es crítico, permitir guardar de todas formas
                # Solo log warning
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Cliente {self.id}: Teléfono {self.telefono} no pudo ser validado "
                    f"con libphonenumber (país: {pais})"
                )
