from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

@login_required  
def test_configuracion(request):
    return HttpResponse("""
    <html>
    <body>
        <h1>🔧 Configuración del Taller - FUNCIONA!</h1>
        <h2>Usuario: {}</h2>
        <p><a href="/configuracion/mecanicos/">Ir a Mecánicos</a></p>
        <p><a href="/admin/">Ir a Admin</a></p>
        <p><a href="/documentos/">Ir a Documentos</a></p>
    </body>
    </html>
    """.format(request.user.username))

@login_required
def test_mecanicos(request):
    from taller.models.perfilusuario import PerfilUsuario
    from taller.models.mecanico import Mecanico
    
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
        empresa = perfil.empresa
        mecanicos = Mecanico.objects.filter(empresa=empresa)
        
        mecanicos_html = ""
        for m in mecanicos:
            status = "✅ ACTIVO" if m.activo else "❌ INACTIVO"
            mecanicos_html += f"<li>{status} {m.nombre}</li>"
        
        if not mecanicos_html:
            mecanicos_html = "<li>No hay mecánicos registrados</li>"
        
    except Exception as e:
        mecanicos_html = f"<li>Error: {e}</li>"
        empresa = None
    
    return HttpResponse(f"""
    <html>
    <body>
        <h1>🧑‍🔧 Mecánicos del Taller - FUNCIONA!</h1>
        <h2>Usuario: {request.user.username}</h2>
        <h3>Empresa: {empresa.nombre_taller if empresa else 'No definida'}</h3>
        <h3>Mecánicos:</h3>
        <ul>
            {mecanicos_html}
        </ul>
        <p><a href="/configuracion/">← Volver a Configuración</a></p>
    </body>
    </html>
    """)
