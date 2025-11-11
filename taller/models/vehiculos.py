from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.urls import reverse

from core.models import TenantScoped

from .clientes import Cliente
from .extras_vehiculo import CajaVehiculo, ColorVehiculo, MotorVehiculo
from .marca import Marca
from .modelo import Modelo


class VehiculoQuerySet(models.QuerySet):
    """QuerySet personalizado para Vehiculo con métodos de conveniencia"""

    def de_empresa(self, empresa):
        """Filtrar por empresa"""
        return self.filter(empresa=empresa)

    def de_cliente(self, cliente_id):
        """Filtrar por cliente"""
        return self.filter(cliente_id=cliente_id)

    def con_vin(self):
        """Filtrar vehículos que tienen VIN"""
        return self.exclude(Q(vin__isnull=True) | Q(vin=""))


class Vehiculo(TenantScoped):
    # empresa viene de TenantScoped (inicialmente nullable en migración)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)

    # Campo marca flexible: puede ser ForeignKey a Marca (Chile) o CharField (USA catálogo global)
    marca = models.ForeignKey(
        Marca,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Marca del vehículo (Chile: referencia a modelo Marca, USA: texto del catálogo)",
    )
    marca_texto = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Marca como texto (para USA catálogo global)",
    )

    # Campo modelo flexible: puede ser ForeignKey a Modelo (Chile) o CharField (USA catálogo global)
    modelo = models.ForeignKey(
        Modelo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Modelo del vehículo (Chile: referencia a modelo Modelo, USA: texto del catálogo)",
    )
    modelo_texto = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        help_text="Modelo como texto (para USA catálogo global)",
    )

    patente = models.CharField(max_length=20, db_index=True)
    anio = models.PositiveIntegerField(verbose_name="Año")
    color = models.ForeignKey(ColorVehiculo, on_delete=models.SET_NULL, null=True, blank=True)
    vin = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    motor = models.ForeignKey(MotorVehiculo, on_delete=models.SET_NULL, null=True, blank=True)
    caja = models.ForeignKey(CajaVehiculo, on_delete=models.SET_NULL, null=True, blank=True)
    millas = models.PositiveIntegerField(blank=True, null=True, verbose_name="Millas/Kilometraje")

    objects = VehiculoQuerySet.as_manager()

    def __str__(self):
        # Mostrar marca y modelo según el sistema usado
        marca_str = self.get_marca_display()
        modelo_str = self.get_modelo_display()
        return f"{self.patente} - {marca_str} {modelo_str}".strip()

    def get_marca_display(self):
        """Obtener el nombre de la marca según el sistema usado"""
        if self.marca_texto:
            return self.marca_texto
        elif self.marca:
            return str(self.marca)
        return "Sin marca"

    def get_modelo_display(self):
        """Obtener el nombre del modelo según el sistema usado"""
        if self.modelo_texto:
            return self.modelo_texto
        elif self.modelo:
            return str(self.modelo)
        return "Sin modelo"

    def display_label(self):
        """Helper de etiqueta para listar en el select AJAX"""
        parts = []
        if self.patente:
            parts.append(self.patente)
        elif self.vin:
            parts.append(self.vin)

        marca = self.get_marca_display()
        modelo = self.get_modelo_display()

        if marca and marca != "Sin marca":
            parts.append(marca)
        if modelo and modelo != "Sin modelo":
            parts.append(modelo)
        if self.anio:
            parts.append(str(self.anio))

        return " · ".join(parts) or f"Vehículo {self.pk}"

    def clean(self):
        """Validaciones de coherencia para evitar datos inconsistentes"""
        super().clean()

        # 1) Empresa coherente con cliente
        if self.empresa_id and self.cliente_id and self.cliente.empresa_id != self.empresa_id:
            raise ValidationError(
                "El cliente del vehículo debe pertenecer a la misma empresa del vehículo."
            )

        # 2) Reglas de país por empresa (siempre deberíamos tener empresa con TenantScoped)
        pais = getattr(getattr(self, "empresa", None), "pais", None)

        # En USA normalmente la patente es menos fiable que el VIN: acepta patente vacía,
        # pero exige al menos un identificador (VIN o patente) en cualquier país.
        if not (self.vin or self.patente):
            raise ValidationError("Debe registrar al menos VIN o Patente.")

        # 3) Consistencia marca/modelo (modo CL vs modo texto USA)
        # Si usas catálogos FK en CL, evita mezclar con *_texto.
        if pais == "CL":
            if self.marca_texto or self.modelo_texto:
                raise ValidationError("En Chile use marca/modelo del catálogo (no *_texto).")
        elif pais == "US":
            # En USA permitimos *_texto. Si además vienen FK, está bien si quieres híbrido;
            # si NO lo quieres, puedes forzar a que sólo se usen *_texto:
            # if self.marca_id or self.modelo_id:
            #     raise ValidationError("En USA use marca_texto/modelo_texto (no FK).")
            pass

        # 4) Coherencia motor/caja con empresa (y con modelo si corresponde)
        if (
            self.motor_id
            and hasattr(self.motor, "empresa_id")
            and self.motor.empresa_id != self.empresa_id
        ):
            raise ValidationError("El motor seleccionado no pertenece a la empresa.")
        if (
            self.caja_id
            and hasattr(self.caja, "empresa_id")
            and self.caja.empresa_id != self.empresa_id
        ):
            raise ValidationError("La caja seleccionada no pertenece a la empresa.")

        # Si en CL tus motores/cajas están ligados a un Modelo específico, valida eso:
        if pais == "CL" and self.modelo_id:
            if (
                self.motor_id
                and hasattr(self.motor, "modelo_id")
                and self.motor.modelo_id
                and self.motor.modelo_id != self.modelo_id
            ):
                raise ValidationError("El motor no corresponde al modelo seleccionado.")
            if (
                self.caja_id
                and hasattr(self.caja, "modelo_id")
                and self.caja.modelo_id
                and self.caja.modelo_id != self.modelo_id
            ):
                raise ValidationError("La caja no corresponde al modelo seleccionado.")

    def get_absolute_url(self):  # usado por CreateView en tests
        try:
            # Usar el namespace por defecto (chile) como fallback
            # Las vistas deben usar country_url para generar URLs correctas
            return reverse("chile:taller:vehiculos:ver_vehiculo", args=[self.pk])
        except Exception:
            return "/vehiculos/"  # fallback seguro

    class Meta(TenantScoped.Meta):
        ordering = ["marca", "modelo", "patente"]
        verbose_name = "Vehículo"
        constraints = [
            models.UniqueConstraint(fields=["empresa", "patente"], name="uq_empresa_patente"),
            models.UniqueConstraint(
                fields=["empresa", "vin"],
                condition=Q(vin__isnull=False) & ~Q(vin=""),
                name="uq_empresa_vin_present",
            ),
        ]
        indexes = [
            models.Index(fields=["empresa"]),
            models.Index(fields=["empresa", "patente"]),
            models.Index(fields=["empresa", "vin"]),
            models.Index(
                fields=["empresa", "cliente"]
            ),  # ✅ CRÍTICO: Para endpoint vehiculos-por-cliente
            models.Index(fields=["marca_texto"]),  # Índice para búsquedas por marca texto
            models.Index(fields=["modelo_texto"]),  # Índice para búsquedas por modelo texto
        ]
