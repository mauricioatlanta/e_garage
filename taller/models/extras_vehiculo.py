from django.core.validators import RegexValidator
from django.db import models
from django.db.models.functions import Lower

# from taller.models.empresa import Empresa  # Descomenta cuando migres a multi-tenant completo
from .modelo import Modelo

hex_validator = RegexValidator(
    regex=r"^#(?:[0-9a-fA-F]{3}){1,2}$",
    message="Usa un código hex válido, ej: #FF0000 o #F00",
)


class ColorVehiculo(models.Model):
    """
    Colores de vehículos con scoping por país (y opcionalmente por empresa).
    Permite tener "Blanco" en CL y "White" en US sin colisiones.
    """

    # empresa = models.ForeignKey(
    #     Empresa, null=True, blank=True, on_delete=models.CASCADE,
    #     related_name="colores", db_index=True
    # )
    country = models.CharField(
        max_length=2,
        default="CL",
        choices=[("CL", "Chile"), ("US", "Estados Unidos"), ("MX", "México")],
        db_index=True,
        verbose_name="País",
    )
    nombre = models.CharField(max_length=50)  # ← SIN unique=True global
    hex = models.CharField(
        max_length=7,
        blank=True,
        null=True,
        validators=[hex_validator],
        help_text="Código de color hexadecimal (#FF0000)",
    )

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Color"
        verbose_name_plural = "Colores"
        constraints = [
            # Unicidad por país + nombre case-insensitive
            models.UniqueConstraint(
                Lower("nombre"),
                "country",
                name="uniq_color_country_lowernombre",
            ),
            # Para multi-tenant estricto (empresa), reemplaza el constraint de arriba con:
            # models.UniqueConstraint(
            #     Lower("nombre"), "country", "empresa",
            #     name="uniq_color_empresa_country_lowernombre",
            # ),
        ]
        indexes = [
            models.Index(fields=["country", "nombre"]),
        ]

    def __str__(self):
        return self.nombre

    @classmethod
    def scoped(cls, country="CL", empresa=None):
        """Devuelve queryset filtrado por país (y opcionalmente empresa)"""
        qs = cls.objects.filter(country=country)
        # if empresa is not None:
        #     qs = qs.filter(empresa=empresa)
        return qs

    @classmethod
    def ensure_defaults_for_country(cls, country="CL", empresa=None):
        """
        Crea (si faltan) colores base para un país/empresa, sin duplicar.
        Llamar antes de get_colores_para_pais() para garantizar seed.
        """
        seed = {
            "CL": [
                "Blanco",
                "Negro",
                "Rojo",
                "Azul",
                "Verde",
                "Amarillo",
                "Gris",
                "Plateado",
                "Dorado",
                "Café",
                "Morado",
                "Naranja",
            ],
            "US": [
                "White",
                "Black",
                "Red",
                "Blue",
                "Green",
                "Yellow",
                "Gray",
                "Silver",
                "Gold",
                "Brown",
                "Purple",
                "Orange",
            ],
            "MX": [
                "Blanco",
                "Negro",
                "Rojo",
                "Azul",
                "Verde",
                "Amarillo",
                "Gris",
                "Plateado",
                "Dorado",
                "Café",
                "Morado",
                "Naranja",
            ],
        }.get(country, [])

        created = []
        for nombre in seed:
            kwargs = {"nombre": nombre, "country": country}
            # if empresa: kwargs["empresa"] = empresa
            obj, _ = cls.objects.get_or_create(**kwargs)
            created.append(obj)
        return created

    @classmethod
    def get_colores_para_pais(cls, country="CL", empresa=None):
        """
        Obtiene colores para el país (y empresa) especificado.
        Garantiza seed automático pero SIEMPRE retorna scoped.
        """
        # Garantiza que existan colores base
        cls.ensure_defaults_for_country(country, empresa)
        # SIEMPRE retorna filtrado por país (y empresa si aplica)
        return cls.scoped(country, empresa).order_by("nombre")


class MotorVehiculo(models.Model):
    """
    Motores de vehículos con scoping por país (y opcionalmente por empresa).
    Asociados a modelos via M2M.
    """

    # empresa = models.ForeignKey(
    #     Empresa, null=True, blank=True, on_delete=models.CASCADE,
    #     related_name="motores", db_index=True
    # )
    country = models.CharField(
        max_length=2,
        default="CL",
        choices=[("CL", "Chile"), ("US", "Estados Unidos"), ("MX", "México")],
        db_index=True,
        verbose_name="País",
    )
    nombre = models.CharField(max_length=100)
    modelos = models.ManyToManyField(Modelo, related_name="motores", blank=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Motor"
        verbose_name_plural = "Motores"
        constraints = [
            # Evita duplicar motores por país (case-insensitive)
            models.UniqueConstraint(
                Lower("nombre"),
                "country",
                name="uniq_motor_country_lowernombre",
            ),
            # Para multi-tenant estricto (empresa):
            # models.UniqueConstraint(
            #     Lower("nombre"), "country", "empresa",
            #     name="uniq_motor_empresa_country_lowernombre",
            # ),
        ]
        indexes = [
            models.Index(fields=["country", "nombre"]),
        ]

    def __str__(self):
        return self.nombre

    @classmethod
    def scoped(cls, country="CL", empresa=None):
        """Devuelve queryset filtrado por país (y opcionalmente empresa)"""
        qs = cls.objects.filter(country=country)
        # if empresa is not None:
        #     qs = qs.filter(empresa=empresa)
        return qs


class MotorVehiculoEmpresa(models.Model):
    """Motor custom privado de una empresa para un modelo concreto."""

    empresa = models.ForeignKey(
        "taller.Empresa",
        on_delete=models.CASCADE,
        related_name="motores_privados",
        db_index=True,
    )
    modelo = models.ForeignKey(
        Modelo,
        on_delete=models.CASCADE,
        related_name="motores_privados",
        db_index=True,
    )
    country = models.CharField(
        max_length=2,
        default="CL",
        choices=[("CL", "Chile"), ("US", "Estados Unidos"), ("MX", "México")],
        db_index=True,
        verbose_name="País",
    )
    nombre = models.CharField(max_length=100)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Motor privado de empresa"
        verbose_name_plural = "Motores privados de empresa"
        constraints = [
            models.UniqueConstraint(
                Lower("nombre"),
                "empresa",
                "modelo",
                "country",
                name="uniq_motor_empresa_modelo_country_lowernombre",
            ),
        ]
        indexes = [
            models.Index(fields=["empresa", "modelo", "country", "nombre"]),
        ]

    def __str__(self):
        return self.nombre


class CajaVehiculo(models.Model):
    """
    Cajas de transmisión de vehículos con scoping por país (y opcionalmente por empresa).
    Asociadas a modelos via M2M.
    """

    # empresa = models.ForeignKey(
    #     Empresa, null=True, blank=True, on_delete=models.CASCADE,
    #     related_name="cajas", db_index=True
    # )
    country = models.CharField(
        max_length=2,
        default="CL",
        choices=[("CL", "Chile"), ("US", "Estados Unidos"), ("MX", "México")],
        db_index=True,
        verbose_name="País",
    )
    nombre = models.CharField(max_length=100)
    modelos = models.ManyToManyField(Modelo, related_name="cajas", blank=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Caja"
        verbose_name_plural = "Cajas"
        constraints = [
            # Evita duplicar cajas por país (case-insensitive)
            models.UniqueConstraint(
                Lower("nombre"),
                "country",
                name="uniq_caja_country_lowernombre",
            ),
            # Para multi-tenant estricto (empresa):
            # models.UniqueConstraint(
            #     Lower("nombre"), "country", "empresa",
            #     name="uniq_caja_empresa_country_lowernombre",
            # ),
        ]
        indexes = [
            models.Index(fields=["country", "nombre"]),
        ]

    def __str__(self):
        return self.nombre

    @classmethod
    def scoped(cls, country="CL", empresa=None):
        """Devuelve queryset filtrado por país (y opcionalmente empresa)"""
        qs = cls.objects.filter(country=country)
        # if empresa is not None:
        #     qs = qs.filter(empresa=empresa)
        return qs


class CajaVehiculoEmpresa(models.Model):
    """Caja/transmisión custom privada de una empresa para un modelo concreto."""

    empresa = models.ForeignKey(
        "taller.Empresa",
        on_delete=models.CASCADE,
        related_name="cajas_privadas",
        db_index=True,
    )
    modelo = models.ForeignKey(
        Modelo,
        on_delete=models.CASCADE,
        related_name="cajas_privadas",
        db_index=True,
    )
    country = models.CharField(
        max_length=2,
        default="CL",
        choices=[("CL", "Chile"), ("US", "Estados Unidos"), ("MX", "México")],
        db_index=True,
        verbose_name="País",
    )
    nombre = models.CharField(max_length=100)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Caja privada de empresa"
        verbose_name_plural = "Cajas privadas de empresa"
        constraints = [
            models.UniqueConstraint(
                Lower("nombre"),
                "empresa",
                "modelo",
                "country",
                name="uniq_caja_empresa_modelo_country_lowernombre",
            ),
        ]
        indexes = [
            models.Index(fields=["empresa", "modelo", "country", "nombre"]),
        ]

    def __str__(self):
        return self.nombre
