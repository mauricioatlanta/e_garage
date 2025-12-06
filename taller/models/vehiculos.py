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

    @property
    def kilometraje_actual(self):
        """
        Devuelve el kilometraje más reciente registrado para este vehículo.

        Returns:
            int: El kilometraje más reciente, o 0 si no hay registros.
        """
        try:
            registro = self.historial_kilometraje.first()  # Usa el ordering de KilometrajeRegistro
            return registro.kilometraje if registro else 0
        except Exception:
            # Fallback en caso de error (por ejemplo, si el modelo aún no existe)
            return 0

    def kilometros_recorridos_desde_documento(self, documento_original):
        """
        Calcula los kilómetros recorridos desde un documento original hasta el kilometraje actual.
        Útil para verificar garantías.

        Args:
            documento_original: Documento de la reparación original

        Returns:
            dict: {
                'kilometros_recorridos': int,
                'kilometraje_original': int,
                'kilometraje_actual': int,
                'dias_transcurridos': int o None
            }
        """
        from taller.models import KilometrajeRegistro

        # Obtener registro del documento original
        try:
            registro_original = documento_original.registro_kilometraje
        except Exception:
            registro_original = None

        if not registro_original:
            return {
                "kilometros_recorridos": None,
                "kilometraje_original": None,
                "kilometraje_actual": self.kilometraje_actual,
                "dias_transcurridos": None,
                "error": "No se encontró registro de kilometraje en el documento original",
            }

        km_actual = self.kilometraje_actual
        km_original = registro_original.kilometraje
        km_recorridos = km_actual - km_original

        # Calcular días transcurridos
        dias = None
        if registro_original.fecha_registro:
            from django.utils import timezone

            delta = timezone.now() - registro_original.fecha_registro
            dias = delta.days

        return {
            "kilometros_recorridos": km_recorridos,
            "kilometraje_original": km_original,
            "kilometraje_actual": km_actual,
            "dias_transcurridos": dias,
            "fecha_original": registro_original.fecha_registro,
        }

    def estadisticas_uso(self):
        """
        Calcula estadísticas de uso del vehículo basadas en el historial de kilometraje.

        Returns:
            dict: {
                'total_registros': int,
                'km_promedio_entre_servicios': float,
                'dias_promedio_entre_servicios': float,
                'km_total_recorridos': int,
                'fecha_primer_registro': datetime o None,
                'fecha_ultimo_registro': datetime o None
            }
        """
        registros = self.historial_kilometraje.all()
        total_registros = registros.count()

        if total_registros < 2:
            return {
                "total_registros": total_registros,
                "km_promedio_entre_servicios": None,
                "dias_promedio_entre_servicios": None,
                "km_total_recorridos": self.kilometraje_actual,
                "fecha_primer_registro": (
                    registros.last().fecha_registro if registros.exists() else None
                ),
                "fecha_ultimo_registro": (
                    registros.first().fecha_registro if registros.exists() else None
                ),
            }

        # Calcular diferencias entre registros consecutivos
        km_diferencias = []
        dias_diferencias = []

        registros_ordenados = list(registros.order_by("fecha_registro"))

        for i in range(1, len(registros_ordenados)):
            anterior = registros_ordenados[i - 1]
            actual = registros_ordenados[i]

            km_diff = actual.kilometraje - anterior.kilometraje
            if km_diff > 0:  # Solo contar si es positivo (evitar errores de datos)
                km_diferencias.append(km_diff)

            if anterior.fecha_registro and actual.fecha_registro:
                delta = actual.fecha_registro - anterior.fecha_registro
                dias_diferencias.append(delta.days)

        km_promedio = sum(km_diferencias) / len(km_diferencias) if km_diferencias else None
        dias_promedio = sum(dias_diferencias) / len(dias_diferencias) if dias_diferencias else None

        return {
            "total_registros": total_registros,
            "km_promedio_entre_servicios": round(km_promedio, 2) if km_promedio else None,
            "dias_promedio_entre_servicios": round(dias_promedio, 2) if dias_promedio else None,
            "km_total_recorridos": self.kilometraje_actual,
            "fecha_primer_registro": (
                registros_ordenados[0].fecha_registro if registros_ordenados else None
            ),
            "fecha_ultimo_registro": (
                registros_ordenados[-1].fecha_registro if registros_ordenados else None
            ),
        }

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
