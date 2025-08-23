
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Index
from decimal import Decimal
from django.utils import timezone
from django.utils.translation import gettext_lazy as _  # 👈 Para traducciones
from core.models import TenantScoped
from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo
from taller.models.mixins import AuditMixin
class Documento(AuditMixin, models.Model):
	empresa = models.ForeignKey('taller.Empresa', on_delete=models.CASCADE, related_name='documentos')
	tecnico_responsable = models.ForeignKey(
		"taller.Tecnico", null=True, blank=True,
		on_delete=models.SET_NULL, related_name="documentos_responsables"
	)
	tipo   = models.CharField(max_length=4, choices=[
		("PRES", _("Presupuesto")),
		("OT",   _("Orden de trabajo")),
		("FAC",  _("Factura")),
		("BOL",  _("Boleta"))
	], db_index=True)
	numero = models.PositiveIntegerField(null=True, blank=True, db_index=True)
	estado = models.CharField(max_length=12, default="DRAFT", db_index=True)
	fecha_emision = models.DateField(default=timezone.now, editable=True, db_index=True)
	cliente  = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="documentos", db_index=True)
	vehiculo = models.ForeignKey(Vehiculo, on_delete=models.SET_NULL, null=True, blank=True, related_name="documentos")
	moneda  = models.CharField(max_length=3, default="CLP")
	country = models.CharField(max_length=2, default="CL")
	neto_repuestos   = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
	neto_servicios   = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
	neto_otros_servicios = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
	descuento        = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
	tax_rate_applied = models.DecimalField(max_digits=5,  decimal_places=2, default=Decimal('0.00'))
	tax_amount       = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
	total            = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
	created_at = models.DateTimeField(default=timezone.now)

	def clean(self):
		super().clean()
		empresa_id = getattr(self, 'empresa_id', None)
		tecnico = getattr(self, 'tecnico_responsable', None)
		tecnico_empresa_id = getattr(tecnico, 'empresa_id', None) if tecnico else None
		if empresa_id is not None and tecnico_empresa_id is not None and empresa_id != tecnico_empresa_id:
			raise ValidationError("El técnico responsable debe pertenecer a la misma empresa del documento.")

	@property
	def numero_documento(self):
		"""Retorna el número de documento con prefijo según tipo y país"""
		if not self.numero:
			return None
		
		# Prefijos para Chile (CL)
		prefijos_cl = {
			'PRES': 'E',    # Estimado
			'OT': 'OT',     # Orden de Trabajo  
			'FAC': 'F',     # Factura
			'BOL': 'B'      # Boleta
		}
		
		# Prefijos para USA
		prefijos_us = {
			'PRES': 'E',    # Estimate
			'OT': 'WO',     # Work Order
			'FAC': 'I',     # Invoice
			'BOL': 'I'      # Invoice (no hay boletas en USA)
		}
		
		prefijos = prefijos_us if self.country == 'US' else prefijos_cl
		prefijo = prefijos.get(self.tipo, self.tipo)
		
		return f"{prefijo}-{self.numero:03d}"

	def generar_numero_documento(self):
		"""Genera el próximo número secuencial para el tipo de documento"""
		if self.numero:
			return self.numero
			
		# Buscar el último número para este tipo de documento en esta empresa
		ultimo_doc = Documento.objects.filter(
			empresa=self.empresa,
			tipo=self.tipo
		).order_by('-numero').first()
		
		if ultimo_doc and ultimo_doc.numero:
			self.numero = ultimo_doc.numero + 1
		else:
			self.numero = 1
			
		return self.numero

	def save(self, *args, **kwargs):
		"""Override save para generar número automáticamente"""
		if not self.numero:
			self.generar_numero_documento()
		super().save(*args, **kwargs)

	@property
	def tipo_documento(self):
		return self.tipo

	@property
	def incluir_iva(self):
		return self.tax_rate_applied > 0

	def total_repuestos(self):
		# Calcular usando campos reales de BD (cantidad * precio_unitario * (1 - descuento/100))
		from django.db.models import Sum, F, Value, DecimalField
		from django.db.models.functions import Coalesce
		return (
			self.lineas_repuesto.aggregate(
				total=Coalesce(
					Sum(
						F('cantidad') * F('precio_unitario') * (1 - F('descuento') / 100),
						output_field=DecimalField(max_digits=12, decimal_places=2)
					),
					Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))
				)
			)['total'] or 0
		)

	def total_servicios(self):
		# Calcular usando campos reales de BD (cantidad * precio_unitario * (1 - descuento/100))
		from django.db.models import Sum, F, Value, DecimalField
		from django.db.models.functions import Coalesce
		return (
			self.lineas_servicio.aggregate(
				total=Coalesce(
					Sum(
						F('cantidad') * F('precio_unitario') * (1 - F('descuento') / 100),
						output_field=DecimalField(max_digits=12, decimal_places=2)
					),
					Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))
				)
			)['total'] or 0
		)

	def total_otros_servicios(self):
		# LineaOtroServicio no siempre tiene 'subtotal'; calculamos precio_cliente * cantidad
		from django.db.models import Sum, F, Value, DecimalField
		from django.db.models.functions import Coalesce
		return (
			self.lineas_otro_servicio.aggregate(
				total=Coalesce(
					Sum(
						F('precio_cliente') * F('cantidad'),
						output_field=DecimalField(max_digits=12, decimal_places=2)
					),
					Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))
				)
			)['total'] or 0
		)

	def iva(self):
		subtotal = self.total_repuestos() + self.total_servicios() + self.total_otros_servicios() - float(self.descuento)
		return subtotal * float(self.tax_rate_applied) / 100 if self.incluir_iva else 0

	def total_general(self):
		return (self.total_repuestos() or 0) + (self.total_servicios() or 0) + (self.total_otros_servicios() or 0)

	def recalcular_totales(self):
		"""Recalcula y actualiza los totales del documento aplicando IVA solo a repuestos"""
		from decimal import Decimal
		
		# Calcular subtotales
		self.neto_repuestos = Decimal(str(self.total_repuestos() or 0))
		self.neto_servicios = Decimal(str(self.total_servicios() or 0))
		self.neto_otros_servicios = Decimal(str(self.total_otros_servicios() or 0))
		
		# Subtotal antes de IVA
		subtotal_antes_iva = self.neto_repuestos + self.neto_servicios + self.neto_otros_servicios - self.descuento
		
		# IVA solo sobre repuestos (regla de negocio)
		base_iva = self.neto_repuestos
		self.tax_rate_applied = Decimal('19.00')  # 19% IVA en Chile
		self.tax_amount = base_iva * self.tax_rate_applied / Decimal('100')
		
		# Total final
		self.total = subtotal_antes_iva + self.tax_amount
		
		# Guardar cambios
		self.save(update_fields=['neto_repuestos', 'neto_servicios', 'neto_otros_servicios', 'tax_rate_applied', 'tax_amount', 'total'])

	# Propiedades retrocompatibles para compatibilidad con código y plantillas antiguas
	@property
	def repuestos(self):
		return self.lineas_repuesto

	@property
	def servicios(self):
		return self.lineas_servicio

	@property
	def otros_servicios(self):
		return self.lineas_otro_servicio

	class Meta:
		app_label = "taller"
		verbose_name = _("Documento")
		verbose_name_plural = _("Documentos")
		indexes = [
			models.Index(fields=["empresa", "fecha_emision"]),
			models.Index(fields=["tecnico_responsable"]),
		]
