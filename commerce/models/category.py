from django.db import models
from django.utils.text import slugify

from core.models import TenantScoped


class CommerceCategory(TenantScoped):
    """
    Categoría pública del catálogo Commerce.
    Capa separada de CategoriaRepuesto (ERP).
    Puede vincularse a una CategoriaRepuesto via 1:1 opcional, o existir de forma independiente.
    """
    categoria_erp = models.OneToOneField(
        "taller.CategoriaRepuesto",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="commerce_category",
    )
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="children",
    )
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140)
    description = models.TextField(blank=True, default="")
    image = models.ImageField(upload_to="commerce/categories/", null=True, blank=True)
    is_active = models.BooleanField(default=True)
    # SEO
    meta_title = models.CharField(max_length=70, blank=True, default="")
    meta_description = models.CharField(max_length=160, blank=True, default="")

    class Meta(TenantScoped.Meta):
        verbose_name = "Categoría Commerce"
        verbose_name_plural = "Categorías Commerce"
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "slug"],
                name="uq_commerce_category_empresa_slug",
            )
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:140] or f"cat-{self.pk or 'new'}"
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("commerce:category", kwargs={"slug": self.slug})
