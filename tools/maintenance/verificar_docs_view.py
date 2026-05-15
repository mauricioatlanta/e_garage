from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from django.http import HttpResponse

from taller.models import Documento, Empresa


@staff_member_required
def verificar_documentos(request):
    """Vista para verificar el estado de los documentos"""

    context = {
        "total_documentos": 0,
        "total_empresas": 0,
        "documentos_recientes": [],
        "error": None,
    }

    try:
        # Conteos básicos
        context["total_documentos"] = Documento.objects.count()
        context["total_empresas"] = Empresa.objects.count()

        # Documentos recientes con anotaciones
        documentos = (
            Documento.objects.annotate(
                rep_count=Count("lineas_repuesto", distinct=True),
                serv_count=Count("lineas_servicio", distinct=True),
                otros_count=Count("lineas_otro_servicio", distinct=True),
            )
            .select_related("empresa", "cliente")
            .order_by("-id")[:10]
        )

        context["documentos_recientes"] = [
            {
                "id": doc.id,
                "numero": getattr(doc, "numero_documento", "N/A"),
                "empresa": doc.empresa.nombre if doc.empresa else "N/A",
                "country": getattr(doc.empresa, "country", "N/A"),
                "cliente": str(doc.cliente) if doc.cliente else "N/A",
                "rep_count": getattr(doc, "rep_count", 0),
                "serv_count": getattr(doc, "serv_count", 0),
                "otros_count": getattr(doc, "otros_count", 0),
                "total": getattr(doc, "total", 0),
            }
            for doc in documentos
        ]

    except Exception as e:
        context["error"] = str(e)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Verificación de Documentos</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .error {{ color: red; background: #ffeeee; padding: 10px; border: 1px solid red; }}
            .success {{ color: green; background: #eeffee; padding: 10px; border: 1px solid green; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <h1>🔍 Verificación de Documentos</h1>

        {'<div class="error">Error: ' + context["error"] + '</div>' if context["error"] else ''}

        <div class="success">
            <h2>📊 Resumen</h2>
            <p><strong>Total Empresas:</strong> {context["total_empresas"]}</p>
            <p><strong>Total Documentos:</strong> {context["total_documentos"]}</p>
        </div>

        <h2>📄 Últimos 10 Documentos</h2>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Número</th>
                    <th>Empresa</th>
                    <th>País</th>
                    <th>Cliente</th>
                    <th># REP</th>
                    <th># SERV</th>
                    <th># OTROS</th>
                    <th>Total</th>
                </tr>
            </thead>
            <tbody>
                {"".join([
                    f"<tr><td>{doc['id']}</td><td>{doc['numero']}</td><td>{doc['empresa']}</td><td>{doc['country']}</td><td>{doc['cliente']}</td><td>{doc['rep_count']}</td><td>{doc['serv_count']}</td><td>{doc['otros_count']}</td><td>${doc['total']}</td></tr>"
                    for doc in context["documentos_recientes"]
                ])}
            </tbody>
        </table>

        <h2>🔧 Acciones</h2>
        <p><a href="/chile/documentos/lista/">Ver Lista Chile</a></p>
        <p><a href="/us/documentos/lista/">Ver Lista USA</a></p>
        <p><a href="/admin/">Admin Django</a></p>

        <h2>🔄 Comandos para ejecutar en terminal</h2>
        <pre>
# Limpiar y crear documentos USA
python manage.py reset_and_seed_docs --hard --count 10 --country US

# Verificar en shell
python manage.py shell
from taller.models import Documento
print("Docs:", Documento.objects.count())
        </pre>
    </body>
    </html>
    """

    return HttpResponse(html)
