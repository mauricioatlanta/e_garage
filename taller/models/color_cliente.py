from django.db import models


class ColorCliente(models.Model):
    """Colores para identificar clientes/subscriptores por país"""

    nombre = models.CharField(max_length=50)
    country = models.CharField(
        max_length=2,
        default="CL",
        choices=[
            ("CL", "Chile"),
            ("US", "Estados Unidos"),
        ],
        verbose_name="País",
        null=True,
        blank=True,
    )

    # Código de color hexadecimal para mostrar en la interfaz
    codigo_color = models.CharField(
        max_length=7,
        default="#00ffe7",
        help_text="Código hexadecimal del color (ej: #00ffe7)",
    )

    # Indica si el color está activo
    activo = models.BooleanField(default=True)

    # Orden de visualización
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["country", "orden", "nombre"]
        verbose_name = "Color Cliente"
        verbose_name_plural = "Colores Cliente"
        db_table = "taller_color_cliente"
        unique_together = [["nombre", "country"]]

    def __str__(self):
        return f"{self.nombre} ({self.get_country_display()})"

    @classmethod
    def get_colores_para_pais(cls, country="CL"):
        """Obtiene colores apropiados para el país especificado"""
        if country == "CL":
            # Crear colores en español para Chile si no existen
            colores_español = [
                ("Blanco", "#ffffff"),
                ("Negro", "#000000"),
                ("Rojo", "#ff0000"),
                ("Azul", "#0000ff"),
                ("Verde", "#00ff00"),
                ("Amarillo", "#ffff00"),
                ("Gris", "#808080"),
                ("Plateado", "#c0c0c0"),
                ("Dorado", "#ffd700"),
                ("Café", "#8b4513"),
                ("Morado", "#800080"),
                ("Naranja", "#ffa500"),
                ("Rosa", "#ffc0cb"),
                ("Celeste", "#87ceeb"),
                ("Turquesa", "#40e0d0"),
                ("Beige", "#f5f5dc"),
                ("Crema", "#fff8dc"),
            ]

            # Crear colores si no existen
            for i, (color_nombre, color_codigo) in enumerate(colores_español):
                cls.objects.get_or_create(
                    nombre=color_nombre,
                    country="CL",
                    defaults={"codigo_color": color_codigo, "orden": i, "activo": True},
                )

            # Filtrar colores que están en español
            colores_españoles = [color[0] for color in colores_español]
            return cls.objects.filter(
                country="CL", nombre__in=colores_españoles, activo=True
            ).order_by("orden", "nombre")

        elif country == "US":
            # Crear colores en inglés para USA si no existen
            colores_english = [
                ("White", "#ffffff"),
                ("Black", "#000000"),
                ("Red", "#ff0000"),
                ("Blue", "#0000ff"),
                ("Green", "#00ff00"),
                ("Yellow", "#ffff00"),
                ("Gray", "#808080"),
                ("Silver", "#c0c0c0"),
                ("Gold", "#ffd700"),
                ("Brown", "#8b4513"),
                ("Purple", "#800080"),
                ("Orange", "#ffa500"),
                ("Pink", "#ffc0cb"),
                ("Sky Blue", "#87ceeb"),
                ("Turquoise", "#40e0d0"),
                ("Beige", "#f5f5dc"),
                ("Cream", "#fff8dc"),
            ]

            # Crear colores si no existen
            for i, (color_nombre, color_codigo) in enumerate(colores_english):
                cls.objects.get_or_create(
                    nombre=color_nombre,
                    country="US",
                    defaults={"codigo_color": color_codigo, "orden": i, "activo": True},
                )

            # Filtrar colores que están en inglés
            colores_english_names = [color[0] for color in colores_english]
            return cls.objects.filter(
                country="US", nombre__in=colores_english_names, activo=True
            ).order_by("orden", "nombre")

        # Fallback: retornar todos los colores activos
        return cls.objects.filter(activo=True).order_by("country", "orden", "nombre")

    @classmethod
    def crear_colores_por_defecto(cls):
        """Crea colores por defecto para ambos países"""
        # Crear colores para Chile
        cls.get_colores_para_pais("CL")
        # Crear colores para USA
        cls.get_colores_para_pais("US")

    def get_css_class(self):
        """Retorna una clase CSS para el color"""
        return f"color-cliente-{self.id}"

    def get_style_attribute(self):
        """Retorna el atributo style para usar en HTML"""
        return f"background-color: {self.codigo_color}; color: {'#000000' if self.codigo_color in ['#ffffff', '#ffff00', '#ffd700', '#ffc0cb', '#87ceeb', '#40e0d0', '#f5f5dc', '#fff8dc'] else '#ffffff'};"
