"""Exportadores de reportes de mecánicos (limpio y probado).

Este archivo reemplaza versiones anteriores desordenadas y garantiza que
las funciones sean sintácticamente válidas y usen `precio_unitario`.
"""

import csv
from datetime import date, timedelta
from io import StringIO

from django.db.models import Count, F, Sum
from django.template.loader import render_to_string

"""Exportadores de reportes de mece1nicos (limpio y probado).

Este archivo provee utilidades para generar PDF/HTML/CSV y mensajes de
resumen para mece1nicos. Las consultas usan los modelos canf3nicos y el
campo `precio_unitario`.
"""

import csv
from datetime import date, timedelta
from io import StringIO

from django.db.models import Count, F, Sum
from django.template.loader import render_to_string

from taller.models.documento import Documento
from taller.models.lineas_documento import LineaServicio
from taller.models.tecnico import Tecnico

"""Exportadores de reportes de mecánicos.

Funciones principales:
- generar_pdf_mecanico: genera HTML o PDF (si weasyprint está presente) para un técnico
- exportar_csv_personalizado: CSV de documentos y servicios
- generar_estadisticas_avanzadas: métricas por técnico
- ReporteMecanicoWhatsApp: mensajes resumen (semanal/mensual)

Las consultas usan los modelos canónicos (LineaServicio) y el campo
normalizado `precio_unitario`. Las funciones usan accesos defensivos para
compatibilidad con código legacy.
"""

import csv
from datetime import date, timedelta
from io import StringIO

from django.db.models import Count, F, Sum
from django.template.loader import render_to_string

from taller.models.documento import Documento
from taller.models.lineas_documento import LineaServicio
from taller.models.tecnico import Tecnico


def _default_date_range(fecha_desde, fecha_hasta, dias=30):
    if not fecha_desde:
        fecha_desde = (date.today() - timedelta(days=dias)).strftime("%Y-%m-%d")
    if not fecha_hasta:
        fecha_hasta = date.today().strftime("%Y-%m-%d")
    return fecha_desde, fecha_hasta


def generar_pdf_mecanico(mecanico_id, fecha_desde=None, fecha_hasta=None):
    """Genera HTML o PDF con métricas para un técnico.

    Retorna bytes del PDF si weasyprint está disponible, en otro caso el HTML
    renderizado (string).
    """
    try:
        from weasyprint import CSS, HTML  # optional
    except Exception:  # pragma: no cover - optional
        HTML = None

    fecha_desde, fecha_hasta = _default_date_range(fecha_desde, fecha_hasta, dias=30)

    mecanico = Tecnico.objects.get(id=mecanico_id)
    documentos = Documento.objects.filter(
        mecanico=mecanico, fecha__range=[fecha_desde, fecha_hasta]
    )
    servicios = LineaServicio.objects.filter(documento__in=documentos)

    total_agg = servicios.aggregate(total=Sum(F("precio_unitario") * F("cantidad")))
    total_generado = total_agg.get("total") or 0

    servicios_top = (
        servicios.values("nombre")
        .annotate(
            cantidad=Count("id"), ingresos=Sum(F("precio_unitario") * F("cantidad"))
        )
        .order_by("-cantidad")[:10]
    )

    docs_por_tipo = (
        documentos.values("tipo_documento")
        .annotate(cantidad=Count("id"))
        .order_by("-cantidad")
    )

    context = {
        "mecanico": mecanico,
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
        "total_documentos": documentos.count(),
        "total_servicios": servicios.count(),
        "total_generado": total_generado,
        "promedio_documento": round(
            total_generado / documentos.count() if documentos.count() > 0 else 0, 0
        ),
        "servicios_top": servicios_top,
        "docs_por_tipo": docs_por_tipo,
        "fecha_generacion": date.today().strftime("%d/%m/%Y"),
    }

    html_string = render_to_string("taller/reportes/pdf_mecanico.html", context)

    css_string = (
        "@page { size: A4; margin: 2cm; }\n"
        "body { font-family: Arial, sans-serif; font-size: 12px; line-height: 1.4; color: #333; }\n"
        ".header { text-align: center; margin-bottom: 30px; padding: 20px; background: linear-gradient(135deg, #f0f8ff, #e6f3ff); border-radius: 10px; }\n"
        ".header h1 { color: #2c3e50; margin: 0; font-size: 24px; }\n"
        "table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }\n"
        "th, td { padding: 8px; border: 1px solid #dee2e6; text-align: left; }\n"
        ".footer { margin-top: 40px; text-align: center; color: #6c757d; font-size: 10px; }\n"
    )

    if HTML:  # pragma: no cover - optional
        css = CSS(string=css_string)
        html = HTML(string=html_string, base_url=".")
        return html.write_pdf(stylesheets=[css])

    return html_string


def exportar_csv_personalizado(mecanico_id=None, fecha_desde=None, fecha_hasta=None):
    """Exporta un CSV con documentos y totales por documento.

    Retorna un string con el contenido CSV.
    """
    fecha_desde, fecha_hasta = _default_date_range(fecha_desde, fecha_hasta, dias=30)

    documentos_qs = Documento.objects.filter(
        fecha__range=[fecha_desde, fecha_hasta], mecanico__isnull=False
    )
    if mecanico_id:
        documentos_qs = documentos_qs.filter(mecanico_id=mecanico_id)

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow(
        [
            "Fecha",
            "Mecánico",
            "Tipo Documento",
            "Número Documento",
            "Cliente",
            "Vehículo",
            "Servicios",
            "Total Generado",
            "Observaciones",
        ]
    )

    for documento in documentos_qs:
        servicios = LineaServicio.objects.filter(documento=documento)
        total = (
            servicios.aggregate(total=Sum(F("precio_unitario") * F("cantidad"))).get(
                "total"
            )
            or 0
        )
        servicios_nombres = ", ".join(servicios.values_list("nombre", flat=True)[:3])

        writer.writerow(
            [
                (
                    documento.fecha.strftime("%d/%m/%Y")
                    if getattr(documento, "fecha", None)
                    else ""
                ),
                (
                    documento.mecanico.nombre
                    if getattr(documento, "mecanico", None)
                    else ""
                ),
                getattr(documento, "tipo_documento", ""),
                getattr(documento, "numero_documento", "") or "",
                (
                    str(getattr(documento, "cliente", ""))
                    if getattr(documento, "cliente", None)
                    else ""
                ),
                (
                    f"{documento.vehiculo.patente} - {documento.vehiculo.modelo}"
                    if getattr(documento, "vehiculo", None)
                    else ""
                ),
                servicios_nombres,
                total,
                getattr(documento, "observaciones", "") or "",
            ]
        )

    return output.getvalue()


def generar_estadisticas_avanzadas(fecha_desde=None, fecha_hasta=None):
    """Genera métricas y estadísticas por técnico dentro del rango dado."""
    fecha_desde, fecha_hasta = _default_date_range(fecha_desde, fecha_hasta, dias=30)

    documentos_qs = Documento.objects.filter(
        fecha__range=[fecha_desde, fecha_hasta], mecanico__isnull=False
    )

    estadisticas = {}
    for mecanico in Tecnico.objects.all():
        docs_mecanico = documentos_qs.filter(mecanico=mecanico)
        servicios_mecanico = LineaServicio.objects.filter(documento__in=docs_mecanico)

        total_docs = docs_mecanico.count()
        total_servicios = servicios_mecanico.count()
        total_generado = (
            servicios_mecanico.aggregate(
                total=Sum(F("precio_unitario") * F("cantidad"))
            ).get("total")
            or 0
        )

        if total_docs > 0:
            promedio_doc = total_generado / total_docs
            promedio_servicio = (
                total_generado / total_servicios if total_servicios > 0 else 0
            )
            servicios_unicos = servicios_mecanico.values("nombre").distinct().count()
            tipos_docs = list(
                docs_mecanico.values("tipo_documento").annotate(count=Count("id"))
            )

            estadisticas[mecanico.id] = {
                "mecanico": mecanico.nombre,
                "total_documentos": total_docs,
                "total_servicios": total_servicios,
                "servicios_unicos": servicios_unicos,
                "total_generado": total_generado,
                "promedio_por_documento": round(promedio_doc, 0),
                "promedio_por_servicio": round(promedio_servicio, 0),
                "tipos_documentos": tipos_docs,
                "eficiencia": round(
                    (total_servicios / total_docs) if total_docs > 0 else 0, 2
                ),
            }

    return estadisticas


class ReporteMecanicoWhatsApp:
    """Genera mensajes resumidos para enviar por WhatsApp o similar."""

    @staticmethod
    def generar_resumen_semanal(mecanico_id):
        mecanico = Tecnico.objects.get(id=mecanico_id)
        fecha_desde = (date.today() - timedelta(days=7)).strftime("%Y-%m-%d")
        fecha_hasta = date.today().strftime("%Y-%m-%d")

        documentos = Documento.objects.filter(
            mecanico=mecanico, fecha__range=[fecha_desde, fecha_hasta]
        )
        servicios = LineaServicio.objects.filter(documento__in=documentos)
        total_generado = (
            servicios.aggregate(total=Sum(F("precio_unitario") * F("cantidad"))).get(
                "total"
            )
            or 0
        )

        servicios_top = (
            servicios.values("nombre")
            .annotate(cantidad=Count("id"))
            .order_by("-cantidad")[:3]
        )

        mensaje = [
            f"🔧 *RESUMEN SEMANAL - {mecanico.nombre.upper()}*",
            "",
            "📅 *Período:* Últimos 7 días",
            "",
            "📊 *MÉTRICAS:*",
            f"• Documentos: {documentos.count()}",
            f"• Servicios: {servicios.count()}",
            f"• Total generado: ${total_generado:,.0f}",
        ]

        mensaje.extend(
            [
                f"{i+1}. {s['nombre']} ({s['cantidad']}x)"
                for i, s in enumerate(servicios_top)
            ]
        )
        mensaje.append("")
        mensaje.append("💪 ¡Sigue así!")
        mensaje.append("_Reporte automático eGarage_")

        return "\n".join(mensaje)

    @staticmethod
    def generar_resumen_mensual(mecanico_id):
        mecanico = Tecnico.objects.get(id=mecanico_id)
        fecha_desde = (date.today() - timedelta(days=30)).strftime("%Y-%m-%d")
        fecha_hasta = date.today().strftime("%Y-%m-%d")

        documentos = Documento.objects.filter(
            mecanico=mecanico, fecha__range=[fecha_desde, fecha_hasta]
        )
        servicios = LineaServicio.objects.filter(documento__in=documentos)
        total_generado = (
            servicios.aggregate(total=Sum(F("precio_unitario") * F("cantidad"))).get(
                "total"
            )
            or 0
        )

        fecha_mes_anterior_inicio = (date.today() - timedelta(days=60)).strftime(
            "%Y-%m-%d"
        )
        fecha_mes_anterior_fin = (date.today() - timedelta(days=30)).strftime(
            "%Y-%m-%d"
        )
        documentos_anterior = Documento.objects.filter(
            mecanico=mecanico,
            fecha__range=[fecha_mes_anterior_inicio, fecha_mes_anterior_fin],
        )
        servicios_anterior = LineaServicio.objects.filter(
            documento__in=documentos_anterior
        )
        total_anterior = (
            servicios_anterior.aggregate(
                total=Sum(F("precio_unitario") * F("cantidad"))
            ).get("total")
            or 0
        )

        crecimiento = 0
        if total_anterior > 0:
            crecimiento = round(
                ((total_generado - total_anterior) / total_anterior) * 100, 1
            )

        emoji_tendencia = "📈" if crecimiento > 0 else "📉" if crecimiento < 0 else "➡️"

        mensaje = [
            f"📊 *RESUMEN MENSUAL - {mecanico.nombre.upper()}*",
            "",
            "📅 *Período:* Últimos 30 días",
            "",
            "💰 *RESULTADOS:*",
            f"• Total generado: ${total_generado:,.0f}",
            f"• Documentos: {documentos.count()}",
            f"• Servicios: {servicios.count()}",
            "",
            f"{emoji_tendencia} *TENDENCIA:*",
            f"• Mes anterior: ${total_anterior:,.0f}",
            f"• Crecimiento: {crecimiento:+.1f}%",
            "",
            f"🏆 ¡Excelente trabajo!",
            "_Reporte eGarage Pro_",
        ]

        return "\n".join(mensaje)
