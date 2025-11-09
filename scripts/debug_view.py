from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from taller.models.clientes import Cliente


def debug_cliente(request, cliente_id):
    """Vista de debug para verificar campos del cliente"""
    cliente = get_object_or_404(
        Cliente.objects.select_related(
            "empresa", "estado_usa", "ciudad_usa", "region", "ciudad"
        ),
        id=cliente_id,
    )

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Debug Cliente {cliente_id}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .debug {{ background: #f0f0f0; padding: 10px; margin: 10px 0; }}
            .success {{ color: green; }}
            .error {{ color: red; }}
        </style>
    </head>
    <body>
        <h1>Debug Cliente {cliente_id}</h1>

        <div class="debug">
            <h2>Información Básica</h2>
            <p><strong>Nombre:</strong> {cliente.nombre} {cliente.apellido}</p>
            <p><strong>Empresa:</strong> {cliente.empresa}</p>
            <p><strong>País de la empresa:</strong> "{cliente.empresa.pais}"</p>
        </div>

        <div class="debug">
            <h2>Evaluación de Condiciones</h2>
            <p><strong>cliente.empresa.pais == 'US':</strong> <span class="{'success' if cliente.empresa.pais == 'US' else 'error'}">{cliente.empresa.pais == 'US'}</span></p>
            <p><strong>cliente.empresa.pais == 'CL':</strong> <span class="{'success' if cliente.empresa.pais == 'CL' else 'error'}">{cliente.empresa.pais == 'CL'}</span></p>
        </div>

        <div class="debug">
            <h2>Campos USA</h2>
            <p><strong>Estado USA:</strong> {cliente.estado_usa or 'None'}</p>
            <p><strong>Ciudad USA:</strong> {cliente.ciudad_usa or 'None'}</p>
            <p><strong>ZIP Code:</strong> {cliente.zipcode or 'None'}</p>
        </div>

        <div class="debug">
            <h2>Campos Chile</h2>
            <p><strong>Región:</strong> {cliente.region or 'None'}</p>
            <p><strong>Ciudad:</strong> {cliente.ciudad or 'None'}</p>
        </div>

        <div class="debug">
            <h2>¿Qué debería mostrar?</h2>
            {'<p class="success">Debería mostrar campos USA (State, City, ZIP)</p>' if cliente.empresa.pais == 'US' else '<p class="error">Debería mostrar campos Chile (Región, Ciudad)</p>'}
        </div>

        <hr>
        <p><a href="/taller/clientes/ver/{cliente_id}/">Ver página original</a></p>
    </body>
    </html>
    """

    return HttpResponse(html)
