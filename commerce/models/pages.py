from django.db import models
from django.utils.text import slugify

from core.models import TenantScoped


PAGE_KEY_CHOICES = [
    ("nosotros", "Quiénes somos"),
    ("faq", "Preguntas frecuentes"),
    ("contacto", "Contacto"),
    ("envios", "Envíos"),
    ("devoluciones", "Cambios y devoluciones"),
    ("custom", "Página personalizada"),
]


class CommerceStaticPage(TenantScoped):
    """
    Página estática del storefront (Nosotros, FAQ, Contacto, etc.).

    key  → identificador semántico; usa 'custom' para páginas libres.
    slug → segmento de URL; permite /promociones, /campañas sin nuevo enum.
    """

    key = models.CharField(max_length=50, choices=PAGE_KEY_CHOICES)
    slug = models.SlugField(max_length=100)
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    position = models.PositiveSmallIntegerField(default=0)
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)

    class Meta:
        verbose_name = "Página estática"
        verbose_name_plural = "Páginas estáticas"
        ordering = ["position", "title"]
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "slug"],
                name="uq_static_page_empresa_slug",
            )
        ]

    def __str__(self):
        return f"{self.title} ({self.empresa})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:100] or self.key
        super().save(*args, **kwargs)


class CommerceFAQ(TenantScoped):
    """
    Pregunta frecuente del storefront.

    Puede vincularse a una CommerceStaticPage de tipo 'faq'
    o existir de forma independiente.
    """

    page = models.ForeignKey(
        CommerceStaticPage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="faqs",
    )
    question = models.CharField(max_length=300)
    answer = models.TextField()
    position = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Pregunta frecuente"
        verbose_name_plural = "Preguntas frecuentes"
        ordering = ["position"]

    def __str__(self):
        return self.question[:80]
