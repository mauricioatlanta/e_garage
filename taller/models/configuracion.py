from decimal import Decimal

from django.db import models

from taller.configuracion.rubros_responsables import (
    DEFAULT_RESPONSABLE_LABEL,
    RESPONSABLE_LABEL_POR_RUBRO,
)


class ConfiguracionEmpresa(models.Model):
    empresa = models.OneToOneField(
        "taller.Empresa", on_delete=models.CASCADE, related_name="config"
    )
    nombre_publico = models.CharField(max_length=150, blank=True, default="")
    tagline = models.CharField(
        max_length=180,
        blank=True,
        default="",
        verbose_name="Eslogan",
        help_text="Texto corto que aparece bajo el nombre",
    )
    logo = models.ImageField(upload_to="logos/", null=True, blank=True)

    # —— CAMPOS DE CONTACTO ——
    # Campo legacy de dirección (deprecar progresivamente)
    direccion = models.CharField(
        max_length=200,
        blank=True,
        default="",
        verbose_name="Dirección",
        help_text="[LEGACY] Dirección de texto plano - Usar legal_address en su lugar",
    )

    # Nueva dirección estructurada usando modelo Address
    legal_address = models.ForeignKey(
        "ubicacion.Address",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="company_legal_addresses",
        verbose_name="Dirección Legal",
        help_text="Dirección legal/fiscal de la empresa (estructurada con ciudad, estado, país)",
    )

    # Feature flag para rollout gradual de Address v2
    use_address_v2 = models.BooleanField(
        default=False,
        verbose_name="Usar Address v2",
        help_text="Activar para usar el nuevo sistema de direcciones estructuradas (Address). "
        "Desactivar para seguir usando campos legacy (direccion, region, ciudad).",
    )

    telefono = models.CharField(
        max_length=40,
        blank=True,
        default="",
        verbose_name="Teléfono",
        help_text="Número de teléfono de contacto (E.164 opcional)",
    )
    email_contacto = models.EmailField(
        blank=True,
        default="",
        verbose_name="Correo Electrónico",
        help_text="Correo electrónico de contacto",
    )
    sitio_web = models.URLField(
        blank=True,
        default="",
        verbose_name="Sitio Web",
        help_text="URL del sitio web de la empresa",
    )

    # —— IMPUESTOS / MONEDA ——
    moneda = models.CharField(max_length=10, default="CLP")  # CLP / USD
    tasa_impuesto = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("19.00"),
        verbose_name="Tasa de Impuesto",
        help_text="IVA/Sales tax %",
    )
    # NOT NULL en BD en varios entornos; default evita fallos en get_or_create sin kwargs extra.
    sales_tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0"),
        verbose_name="Sales tax rate (%)",
        help_text="Tasa de impuesto a ventas (porcentaje); complementa tasa_impuesto donde aplica.",
    )
    aplicar_impuesto_por_defecto = models.BooleanField(
        default=False,
        verbose_name="Aplicar impuesto por defecto",
        help_text="Aplicar IVA/impuesto automáticamente",
    )

    # —— VISUAL / FLAGS ——
    brand_color = models.CharField(
        max_length=7,
        default="#1a202c",
        verbose_name="Color de Marca",
        help_text="Color principal de la marca (hex)",
    )
    dividir_por_tecnico = models.BooleanField(
        default=False,
        verbose_name="Dividir por técnico",
        help_text="Separar trabajos por técnico asignado",
    )

    # —— SWITCHES DE MÓDULOS DOCUMENTO ——
    usa_vehiculos = models.BooleanField(
        default=True,
        verbose_name="Usar módulo de vehículos",
        help_text="Activa la selección y gestión de vehículos en los documentos.",
    )
    usa_servicios = models.BooleanField(
        default=True,
        verbose_name="Usar módulo de servicios",
        help_text="Activa la sección de servicios internos en los documentos.",
    )
    usa_otros_servicios = models.BooleanField(
        default=False,
        verbose_name="Usar módulo de servicios externos",
        help_text="Activa la sección de servicios externos/terceros.",
    )
    usa_kilometraje = models.BooleanField(
        default=False,
        verbose_name="Solicitar kilometraje",
        help_text="Muestra el campo de kilometraje/odómetro en los documentos.",
    )

    # —— TÉCNICO POR DEFECTO (mantener compatibilidad) ——
    tecnico_por_defecto = models.ForeignKey(
        "taller.Tecnico",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="tecnico_por_defecto_de",
    )

    # —— RUBRO PRINCIPAL ——
    RUBRO_CHOICES = [
        ("WORKSHOP", "Taller mecánico integral"),
        ("WORKSHOP_MOTO", "Taller de motos"),
        ("WORKSHOP_HEAVY", "Taller de camiones/buses"),
        ("EXHAUST", "Escapes y mufflers"),
        ("DESARMADURIA", "Desarmaduría / Salvage"),
        ("PARTS", "Casa de repuestos / Autopartes"),
        ("TIRE", "Vulcanización / Neumáticos y llantas"),
        ("BODYSHOP", "Carrocería / Pintura"),
        ("DETAILING", "Lavado, detailing y estética"),
        ("ELECTRIC", "Electricidad / electrónica automotriz"),
        ("GLASS_AUDIO", "Parabrisas, vidrios y audio / accesorios"),
        ("FLEET", "Mantención de flotas empresariales"),
        ("SUSPENSION_STEERING", "Taller de Suspensión y Dirección"),
        ("BRAKES", "Taller de Frenos"),
        ("OBD_DIAGNOSTIC", "Taller de Diagnóstico Computarizado (OBD-II)"),
        ("CLASSIC_CARS", "Taller de Reparación de Vehículos Clásicos"),
        ("AUDIO_ENTERTAINMENT", "Taller de Sistemas de Audio y Entretenimiento Automotriz"),
        ("GAS_CONVERSION", "Taller de Conversiones a Gas"),
        ("FLEET_REPAIR", "Taller de Reparación de Flotas Corporativas"),
        ("BODY_GLASS", "Taller de Carrocería y Reparación de Vidrios"),
        ("TUNING", "Taller de Tuning / Personalización"),
        ("RECYCLING", "Reciclaje / Chatarra electrónica y catalíticos"),
        ("MIXED", "Mixto (multi-rubro — varios giros)"),
    ]

    rubro_principal = models.CharField(
        max_length=30,
        choices=RUBRO_CHOICES,
        default="WORKSHOP",
        verbose_name="Rubro Principal",
        help_text="Rubro principal automotriz de la empresa",
    )
    rubros = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Rubros",
        help_text="Lista de rubros que ofrece el taller (múltiples rubros)",
    )

    # —— ESPECIALIDAD DE RECICLAJE (solo aplica cuando el rubro es RECYCLING) ——
    # Segunda capa bajo rubro_principal="RECYCLING": una recicladora de metales,
    # una compradora de catalíticos y una planta de chatarra electrónica son
    # operativamente distintas aunque compartan el mismo rubro. Mismo convenio
    # que rubro_principal/rubros: recycling_type_principal siempre incluido
    # primero en recycling_types.
    RECYCLING_TYPE_CHOICES = [
        ("METAL_RECYCLING", "Reciclaje de metales"),
        ("CATALYTIC_RECYCLING", "Convertidores catalíticos"),
        ("ELECTRONIC_SCRAP", "Chatarra electrónica"),
        ("AUTO_PARTS_RECYCLING", "Reciclaje de autopartes"),
        ("INDUSTRIAL_SCRAP", "Chatarra industrial"),
    ]

    recycling_type_principal = models.CharField(
        max_length=30,
        choices=RECYCLING_TYPE_CHOICES,
        blank=True,
        null=True,
        verbose_name="Especialidad de reciclaje principal",
        help_text="Solo aplica cuando el rubro es RECYCLING. Especialidad principal del negocio.",
    )
    recycling_types = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Especialidades de reciclaje",
        help_text="Lista de especialidades de reciclaje activas (subconjunto de RECYCLING_TYPE_CHOICES).",
    )

    # —— CONTROL DE MÓDULOS ——
    modules_configured_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Módulos configurados el",
        help_text=(
            "Fecha en que el usuario configuró explícitamente sus módulos de negocio. "
            "Si es null, se mostrará el asistente de migración."
        ),
    )

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def has_completed_business_setup(self) -> bool:
        """
        True si el negocio fue configurado explícitamente por el usuario
        (vía signup o vía onboarding paso 1).
        Usar en lugar de inspeccionar rubro_principal directamente en las vistas.
        """
        return self.modules_configured_at is not None

    def get_effective_rubros(self) -> list:
        """
        Retorna todos los rubros activos: rubro_principal siempre primero,
        seguido de los rubros adicionales sin duplicar.
        Convenio de almacenamiento: rubros[] incluye rubro_principal.
        Este método es la fuente canónica para código que necesita el conjunto completo.
        """
        principal = self.rubro_principal or "WORKSHOP"
        stored = list(self.rubros or [])
        result = [principal]
        for r in stored:
            if r not in result:
                result.append(r)
        return result

    def get_effective_recycling_types(self) -> list:
        """
        Retorna las especialidades de reciclaje activas: recycling_type_principal
        siempre primero, seguido de recycling_types adicionales sin duplicar.
        Lista vacía si no hay recycling_type_principal (empresa no es RECYCLING,
        o aún no configuró su especialidad).
        """
        principal = (self.recycling_type_principal or "").strip()
        if not principal:
            return []
        stored = list(self.recycling_types or [])
        result = [principal]
        for r in stored:
            if r and r not in result:
                result.append(r)
        return result

    def __str__(self):
        if not getattr(self, "empresa", None):
            return "Configuración sin empresa"

        nombre_empresa = (
            self.nombre_publico
            or getattr(self.empresa, "nombre_taller", "")
            or getattr(self.empresa, "empresa", "")
            or "sin nombre"
        )
        return f"Config {self.empresa_id} – {nombre_empresa}"

    def get_responsable_label(self, country="CL"):
        """
        Retorna la etiqueta del campo responsable según el rubro y país.

        Args:
            country: Código de país ('CL', 'US', etc.)

        Returns:
            str: Etiqueta del responsable (ej: "Mecánico responsable", "Vendedor responsable")
        """
        # Obtener la etiqueta base desde el archivo de configuración
        label_base = RESPONSABLE_LABEL_POR_RUBRO.get(
            self.rubro_principal, DEFAULT_RESPONSABLE_LABEL
        )

        # Por ahora, retornamos la etiqueta base (en español)
        # En el futuro se puede agregar traducción por país si es necesario
        return label_base

    def get_secciones_visibles(self):
        """
        Retorna un diccionario indicando qué secciones deben mostrarse según el rubro.

        Returns:
            dict: {
                'repuestos': bool,
                'servicios': bool,
                'otros_servicios': bool,
                'kilometraje': bool,
                'vehiculo': bool,
            }
        """
        secciones = {
            "repuestos": True,
            "servicios": getattr(self, "usa_servicios", True),
            "otros_servicios": getattr(self, "usa_otros_servicios", False),
            "kilometraje": getattr(self, "usa_kilometraje", False),
            "vehiculo": getattr(self, "usa_vehiculos", True),
        }

        # Ajustes según rubro
        if self.rubro_principal == "PARTS":
            # Casa de repuestos: solo repuestos, sin servicios ni kilometraje
            secciones["servicios"] = False
            secciones["otros_servicios"] = False
            secciones["kilometraje"] = False
        elif self.rubro_principal == "RECYCLING":
            # Reciclaje (catalíticos, chatarra u otros materiales): la compra
            # nunca está asociada a un vehículo del cliente ni a servicios
            # internos — el formulario de documento se usa solo para
            # registrar líneas de material comprado.
            secciones["servicios"] = False
            secciones["otros_servicios"] = False
            secciones["kilometraje"] = False
            secciones["vehiculo"] = False
        elif self.rubro_principal == "TIRE":
            # Vulcanización: servicios y repuestos, con kilometraje
            secciones["repuestos"] = True
            secciones["servicios"] = True
            secciones["otros_servicios"] = False
            secciones["kilometraje"] = True
        elif self.rubro_principal == "DETAILING":
            # Lavado/detailing: principalmente servicios, sin repuestos
            secciones["repuestos"] = False
            secciones["servicios"] = True
            secciones["otros_servicios"] = False
            secciones["kilometraje"] = True
        elif self.rubro_principal == "EXHAUST":
            # Escapes: servicios y repuestos
            secciones["repuestos"] = True
            secciones["servicios"] = True
            secciones["otros_servicios"] = False
            secciones["kilometraje"] = True
        elif self.rubro_principal == "GLASS_AUDIO":
            # Parabrisas/audio: servicios y repuestos
            secciones["repuestos"] = True
            secciones["servicios"] = True
            secciones["otros_servicios"] = False
            secciones["kilometraje"] = True

        return secciones

    def get_ui_config(self):
        """
        Retorna configuración de UI para el formulario de documentos.
        """
        secciones = self.get_secciones_visibles()
        return {
            "show_vehicle": secciones.get("vehiculo", True),
            "show_services": secciones.get("servicios", True),
            "show_otros_servicios": secciones.get("otros_servicios", False),
            "show_repuestos": secciones.get("repuestos", True),
            "show_kilometraje": secciones.get("kilometraje", False),
        }

    class Meta:
        verbose_name = "Configuración de Empresa"
        verbose_name_plural = "Configuraciones de Empresas"

    def save(self, *args, **kwargs):
        # Normalización automática de moneda según país
        if not self.moneda and hasattr(self, "empresa") and self.empresa:
            self.moneda = "CLP" if getattr(self.empresa, "pais", "CL") == "CL" else "USD"
        super().save(*args, **kwargs)
