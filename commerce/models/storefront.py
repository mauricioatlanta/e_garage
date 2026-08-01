from django.db import models

from core.models import TenantScoped


class CommerceStorefrontSettings(TenantScoped):
    """
    Configuración de marca y SEO del storefront — un registro por tenant.

    schema_version permite migraciones hacia nuevos temas sin romper storefronts
    existentes: cuando aparezca Theme 2, los registros con schema_version=1
    siguen funcionando con el tema anterior hasta ser migrados explícitamente.
    """

    schema_version = models.PositiveSmallIntegerField(default=1)

    # Branding
    tagline = models.CharField(max_length=200, blank=True)
    primary_color = models.CharField(
        max_length=7, default="#3B82F6", help_text="Hex: #RRGGBB"
    )
    secondary_color = models.CharField(max_length=7, default="#1E40AF")
    accent_color = models.CharField(max_length=7, default="#06B6D4")

    # SEO por defecto del storefront
    seo_title = models.CharField(max_length=70, blank=True)
    seo_description = models.CharField(max_length=160, blank=True)

    # Contacto / Social
    whatsapp_number = models.CharField(max_length=20, blank=True)
    instagram_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)

    class Meta:
        verbose_name = "Configuración de storefront"
        verbose_name_plural = "Configuraciones de storefront"
        constraints = [
            models.UniqueConstraint(
                fields=["empresa"],
                name="uq_storefront_settings_empresa",
            )
        ]

    def __str__(self):
        return f"Storefront settings — {self.empresa}"
