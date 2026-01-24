from django.db.models import (
    Count,
    DecimalField,
    IntegerField,
    OuterRef,
    Subquery,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce
from django.views.generic import ListView

from taller.mixins import CountryLangTemplateMixin  # Agregar import del mixin
from taller.models import Documento, LineaOtroServicio, LineaRepuesto, LineaServicio


class DocumentoListViewBase(CountryLangTemplateMixin, ListView):
    model = Documento
    base_template_name = "documentos/lista_documentos.html"  # usa template resolution
    context_object_name = "documentos"  # ← fijamos el nombre para el template
    paginate_by = 50

    def render_to_response(self, context, **response_kwargs):
        return self.render_country_lang(self.request, context)

    def get_queryset(self):
        empresa = getattr(self.request.user, "empresa", None)
        qs = Documento.objects.all()
        if empresa:
            qs = qs.filter(empresa=empresa)

        # Subquerys a prueba de joins: cuentan por documento sin multiplicaciones
        rep_ct = Subquery(
            LineaRepuesto.objects.filter(documento_id=OuterRef("pk"))
            .values("documento")
            .annotate(c=Count("id"))
            .values("c")[:1],
            output_field=IntegerField(),
        )
        serv_ct = Subquery(
            LineaServicio.objects.filter(documento_id=OuterRef("pk"))
            .values("documento")
            .annotate(c=Count("id"))
            .values("c")[:1],
            output_field=IntegerField(),
        )
        otros_ct = Subquery(
            LineaOtroServicio.objects.filter(documento_id=OuterRef("pk"))
            .values("documento")
            .annotate(c=Count("id"))
            .values("c")[:1],
            output_field=IntegerField(),
        )

        # (Opcional) Subtotales monetarios con Subquery
        rep_sum = Subquery(
            LineaRepuesto.objects.filter(documento_id=OuterRef("pk"))
            .values("documento")
            .annotate(s=Sum("precio_unitario"))
            .values("s")[:1],
            output_field=DecimalField(max_digits=12, decimal_places=2),
        )
        serv_sum = Subquery(
            LineaServicio.objects.filter(documento_id=OuterRef("pk"))
            .values("documento")
            .annotate(s=Sum("precio_unitario"))
            .values("s")[:1],
            output_field=DecimalField(max_digits=12, decimal_places=2),
        )
        otros_sum = Subquery(
            LineaOtroServicio.objects.filter(documento_id=OuterRef("pk"))
            .values("documento")
            .annotate(s=Sum("precio_cliente"))
            .values("s")[:1],
            output_field=DecimalField(max_digits=12, decimal_places=2),
        )

        return (
            qs.select_related("empresa", "cliente", "vehiculo", "tecnico_responsable")
            .annotate(
                rep_count=Coalesce(rep_ct, Value(0), output_field=IntegerField()),
                serv_count=Coalesce(serv_ct, Value(0), output_field=IntegerField()),
                otros_count=Coalesce(otros_ct, Value(0), output_field=IntegerField()),
                sum_rep=Coalesce(
                    rep_sum,
                    Value(0),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                ),
                sum_serv=Coalesce(
                    serv_sum,
                    Value(0),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                ),
                sum_out=Coalesce(
                    otros_sum,
                    Value(0),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                ),
            )
            .order_by("-fecha_emision", "-id")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener el país desde la URL path
        path = self.request.path
        if path.startswith("/cl/"):
            country = "cl"
        elif path.startswith("/us/"):
            country = "us"
        else:
            country = "cl"  # fallback por defecto
        context["country"] = country
        return context
