"""Domain models for the eGarage towing MVP.

The models intentionally live in the ``taller`` Django application.  A towing
order is tenant scoped and keeps the operational, quotation and ledger
concerns separate without duplicating customers or vehicles.
"""

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from taller.gruas.storage import PrivateEvidenceStorage


class TowingUnit(models.Model):
    empresa = models.ForeignKey("taller.Empresa", on_delete=models.CASCADE, related_name="towing_units")
    nombre = models.CharField(max_length=120)
    patente = models.CharField(max_length=20, db_index=True)
    tipo = models.CharField(max_length=40, default="PLATAFORMA")
    capacidad_kg = models.PositiveIntegerField(null=True, blank=True)
    estado = models.CharField(max_length=20, default="ACTIVA", db_index=True)
    kilometraje = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("empresa", "patente"), name="uq_towing_unit_empresa_patente"),
        ]
        indexes = [models.Index(fields=("empresa", "estado"))]

    def __str__(self):
        return f"{self.patente} · {self.nombre}"


class TowingDriver(models.Model):
    empresa = models.ForeignKey("taller.Empresa", on_delete=models.CASCADE, related_name="towing_drivers")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="towing_driver_profiles")
    nombre = models.CharField(max_length=120)
    telefono = models.CharField(max_length=30, blank=True, default="")
    licencia = models.CharField(max_length=60, blank=True, default="")
    licencia_vencimiento = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("empresa", "user"), condition=Q(user__isnull=False), name="uq_towing_driver_empresa_user"),
        ]
        indexes = [models.Index(fields=("empresa", "activo")), models.Index(fields=("user", "activo"))]

    def __str__(self):
        return self.nombre


class TowingOrder(models.Model):
    STATUS_REQUESTED = "SOLICITADA"
    STATUS_QUOTED = "COTIZADA"
    STATUS_ACCEPTED = "ACEPTADA"
    STATUS_ASSIGNED = "ASIGNADA"
    STATUS_EN_ROUTE = "EN_CAMINO"
    STATUS_PICKUP = "EN_RETIRO"
    STATUS_LOADED = "CARGADA"
    STATUS_TRANSIT = "EN_TRASLADO"
    STATUS_DELIVERED = "ENTREGADA"
    STATUS_CLOSED = "CERRADA"
    STATUS_CANCELLED = "CANCELADA"
    STATUS_FAILED = "SALIDA_FALLIDA"
    STATUS_CHOICES = [(v, v.replace("_", " ").title()) for v in (
        STATUS_REQUESTED, STATUS_QUOTED, STATUS_ACCEPTED, STATUS_ASSIGNED,
        STATUS_EN_ROUTE, STATUS_PICKUP, STATUS_LOADED, STATUS_TRANSIT,
        STATUS_DELIVERED, STATUS_CLOSED, STATUS_CANCELLED, STATUS_FAILED,
    )]

    empresa = models.ForeignKey("taller.Empresa", on_delete=models.CASCADE, related_name="towing_orders")
    numero = models.CharField(max_length=32, db_index=True)
    solicitante = models.ForeignKey("taller.Cliente", null=True, blank=True, on_delete=models.PROTECT, related_name="towing_orders_requested")
    vehiculo = models.ForeignKey("taller.Vehiculo", null=True, blank=True, on_delete=models.SET_NULL, related_name="towing_orders")
    patente_snapshot = models.CharField(max_length=20, blank=True, default="")
    vehiculo_snapshot = models.CharField(max_length=180, blank=True, default="")
    pagador_nombre = models.CharField(max_length=160, blank=True, default="")
    receptor_nombre = models.CharField(max_length=160, blank=True, default="")
    origen = models.CharField(max_length=255)
    destino = models.CharField(max_length=255)
    origen_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    origen_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    destino_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    destino_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    planned_start_at = models.DateTimeField(null=True, blank=True)
    planned_end_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_REQUESTED, db_index=True)
    currency = models.CharField(max_length=3, default="CLP")
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    documento = models.ForeignKey("taller.Documento", null=True, blank=True, on_delete=models.SET_NULL, related_name="towing_orders")
    closed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="towing_orders_created")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("empresa", "numero"), name="uq_towing_order_empresa_numero")]
        indexes = [models.Index(fields=("empresa", "status", "created_at")), models.Index(fields=("empresa", "planned_start_at"))]

    def clean(self):
        if self.planned_start_at and self.planned_end_at and self.planned_end_at <= self.planned_start_at:
            raise ValidationError("El término previsto debe ser posterior al inicio previsto.")
        if self.vehiculo and self.vehiculo.empresa_id != self.empresa_id:
            raise ValidationError("El vehículo debe pertenecer a la misma empresa.")
        if self.solicitante and self.solicitante.empresa_id != self.empresa_id:
            raise ValidationError("El cliente debe pertenecer a la misma empresa.")

    @property
    def vigente_quote(self):
        return self.quotes.filter(is_current=True).first()

    def __str__(self):
        return self.numero


class TowingQuote(models.Model):
    STATUS_DRAFT = "DRAFT"
    STATUS_SENT = "SENT"
    STATUS_ACCEPTED = "ACCEPTED"
    STATUS_REJECTED = "REJECTED"
    STATUS_EXPIRED = "EXPIRED"
    STATUS_CHOICES = [(v, v.title()) for v in (STATUS_DRAFT, STATUS_SENT, STATUS_ACCEPTED, STATUS_REJECTED, STATUS_EXPIRED)]

    order = models.ForeignKey(TowingOrder, on_delete=models.CASCADE, related_name="quotes")
    version = models.PositiveIntegerField()
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    is_current = models.BooleanField(default=True)
    currency = models.CharField(max_length=3, default="CLP")
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    net_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    included_km = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    notes = models.TextField(blank=True, default="")
    accepted_at = models.DateTimeField(null=True, blank=True)
    accepted_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="towing_quotes_accepted")
    supersedes = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="superseded_by")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="towing_quotes_created")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("order", "version"), name="uq_towing_quote_order_version"),
            models.UniqueConstraint(fields=("order",), condition=Q(is_current=True), name="uq_towing_quote_current"),
        ]
        ordering = ["-version"]


class TowingAssignment(models.Model):
    order = models.ForeignKey(TowingOrder, on_delete=models.CASCADE, related_name="assignments")
    unit = models.ForeignKey(TowingUnit, on_delete=models.PROTECT, related_name="assignments")
    driver = models.ForeignKey(TowingDriver, on_delete=models.PROTECT, related_name="assignments")
    is_active = models.BooleanField(default=True, db_index=True)
    planned_start_at = models.DateTimeField()
    planned_end_at = models.DateTimeField()
    actual_start_at = models.DateTimeField(null=True, blank=True)
    actual_end_at = models.DateTimeField(null=True, blank=True)
    released_at = models.DateTimeField(null=True, blank=True)
    release_reason = models.CharField(max_length=120, blank=True, default="")
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="towing_assignments_created")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(check=Q(planned_end_at__gt=models.F("planned_start_at")), name="ck_towing_assignment_interval"),
            models.CheckConstraint(check=Q(is_active=True, released_at__isnull=True) | Q(is_active=False), name="ck_towing_assignment_release"),
        ]
        indexes = [models.Index(fields=("unit", "is_active", "planned_start_at")), models.Index(fields=("driver", "is_active", "planned_start_at"))]


class TowingEvent(models.Model):
    order = models.ForeignKey(TowingOrder, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=40)
    from_status = models.CharField(max_length=20, blank=True, default="")
    to_status = models.CharField(max_length=20, blank=True, default="")
    assignment = models.ForeignKey(TowingAssignment, null=True, blank=True, on_delete=models.SET_NULL, related_name="events")
    metadata = models.JSONField(default=dict, blank=True)
    comment = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="towing_events_created")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [models.Index(fields=("order", "created_at"))]


class TowingLedgerEntry(models.Model):
    CHARGE = "CHARGE"
    ADVANCE = "ADVANCE"
    PAYMENT = "PAYMENT"
    REFUND = "REFUND"
    EXPENSE = "EXPENSE"
    EXPENSE_REVERSAL = "EXPENSE_REVERSAL"
    ENTRY_CHOICES = [(v, v.title()) for v in (CHARGE, ADVANCE, PAYMENT, REFUND, EXPENSE, EXPENSE_REVERSAL)]

    order = models.ForeignKey(TowingOrder, on_delete=models.CASCADE, related_name="ledger_entries")
    entry_type = models.CharField(max_length=16, choices=ENTRY_CHOICES)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3, default="CLP")
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    tax_included = models.BooleanField(default=False)
    reference = models.CharField(max_length=120, blank=True, default="")
    reversed_entry = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT, related_name="reversal")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="towing_ledger_entries_created")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [models.CheckConstraint(check=Q(amount__gt=0), name="ck_towing_ledger_positive_amount")]
        indexes = [models.Index(fields=("order", "entry_type", "created_at"))]


class TowingEvidence(models.Model):
    order = models.ForeignKey(TowingOrder, on_delete=models.CASCADE, related_name="evidences")
    assignment = models.ForeignKey(TowingAssignment, null=True, blank=True, on_delete=models.SET_NULL, related_name="evidences")
    kind = models.CharField(max_length=30)
    file = models.FileField(storage=PrivateEvidenceStorage(), upload_to="towing_evidence/%Y/%m/")
    description = models.TextField(blank=True, default="")
    shared_with_customer = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="towing_evidence_created")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=("order", "created_at")), models.Index(fields=("order", "shared_with_customer"))]
