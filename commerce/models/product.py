from django.db import models
from django.utils.text import slugify

from core.models import TenantScoped

from .category import CommerceCategory


class CommerceProduct(TenantScoped):
    """
    Producto público del catálogo Commerce.
    Capa separada de Repuesto (ERP) — vinculada via 1:1.
    El ERP no conoce a CommerceProduct. Commerce no modifica Repuesto.
    """
    repuesto = models.OneToOneField(
        "taller.Repuesto",
        on_delete=models.CASCADE,
        related_name="commerce_product",
    )
    category = models.ForeignKey(
        CommerceCategory,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="products",
    )
    slug = models.SlugField(max_length=280)
    descripcion_larga = models.TextField(blank=True, default="")
    compare_at_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Precio anterior para mostrar tachado. Si está vacío, no se muestra oferta.",
    )
    is_publishable = models.BooleanField(
        default=False,
        help_text="Solo los productos publicables aparecen en el catálogo público.",
    )
    published_at = models.DateTimeField(null=True, blank=True)
    # SEO
    meta_title = models.CharField(max_length=70, blank=True, default="")
    meta_description = models.CharField(max_length=160, blank=True, default="")
    og_image = models.ImageField(upload_to="commerce/og/", null=True, blank=True)

    class Meta(TenantScoped.Meta):
        verbose_name = "Producto Commerce"
        verbose_name_plural = "Productos Commerce"
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "slug"],
                name="uq_commerce_product_empresa_slug",
            )
        ]

    def __str__(self):
        return f"{self.repuesto.part_number or '—'} | {self.repuesto.nombre}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = self.repuesto.part_number or self.repuesto.nombre or str(self.repuesto_id)
            self.slug = slugify(base)[:280] or f"prod-{self.repuesto_id}"
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("commerce:product", kwargs={"slug": self.slug})

    @property
    def precio_venta(self):
        return self.repuesto.precio_venta

    @property
    def stock(self):
        return self.repuesto.cantidad_stock

    @property
    def nombre(self):
        return self.repuesto.nombre

    @property
    def part_number(self):
        return self.repuesto.part_number

    @property
    def primary_image(self):
        return self.images.filter(is_primary=True).first() or self.images.first()

    def tiene_descuento(self):
        return self.compare_at_price and self.compare_at_price > self.precio_venta

    def porcentaje_descuento(self):
        if not self.tiene_descuento():
            return 0
        return int((1 - self.precio_venta / self.compare_at_price) * 100)


class ProductImage(models.Model):
    """Hasta 4 imágenes por CommerceProduct (posición 1-4)."""

    commerce_product = models.ForeignKey(
        CommerceProduct,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(upload_to="commerce/products/")
    alt_text = models.CharField(max_length=160, blank=True, default="")
    is_primary = models.BooleanField(default=False)
    position = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["position"]
        verbose_name = "Imagen de producto"
        verbose_name_plural = "Imágenes de producto"
        constraints = [
            models.CheckConstraint(
                check=models.Q(position__gte=1) & models.Q(position__lte=4),
                name="commerce_productimage_position_1_to_4",
            ),
            models.UniqueConstraint(
                fields=["commerce_product", "position"],
                name="uq_commerce_productimage_position",
            ),
        ]

    def __str__(self):
        return f"{self.commerce_product} — imagen {self.position}"
