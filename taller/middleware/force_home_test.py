"""
Middleware temporal para forzar que la raíz "/" muestre la página de prueba.
Esto asegura que incluso si hay algo interceptando, se muestre eGarage.
"""

import datetime
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin


class ForceHomeTestMiddleware(MiddlewareMixin):
    """
    Intercepta la raíz "/" y devuelve directamente HTML de prueba.
    Esto asegura que se muestre eGarage y no Desarmaduría 2.0.
    """

    def process_request(self, request):
        # Solo interceptar la raíz exacta "/"
        if request.path == "/" and request.method == "GET":
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <title>✅ EGARAGE HOME TEST - {timestamp}</title>
    <style>
        body {{
            background: #020617;
            color: #e5e7eb;
            font-family: system-ui, -apple-system, sans-serif;
            padding: 40px;
            margin: 0;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
        }}
        h1 {{
            font-size: 48px;
            color: #00ff00;
            text-shadow: 0 0 20px #00ff00, 0 0 40px #00ff00;
            margin-bottom: 20px;
        }}
        .success {{
            font-size: 24px;
            color: #00ffff;
            margin: 20px 0;
        }}
        .debug-box {{
            margin-top: 30px;
            padding: 20px;
            background: #1a1a2e;
            border: 3px solid #00ff00;
            border-radius: 10px;
            box-shadow: 0 0 30px rgba(0, 255, 0, 0.5);
        }}
        .debug-box p {{
            margin: 10px 0;
            font-family: 'Courier New', monospace;
        }}
        .big-check {{
            font-size: 60px;
            color: #00ff00;
            text-align: center;
            margin: 20px 0;
        }}
        .middleware-badge {{
            background: #ff6b6b;
            color: white;
            padding: 10px;
            border-radius: 5px;
            font-weight: bold;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="middleware-badge">🔧 SERVIDO DESDE MIDDLEWARE - Esto garantiza que es eGarage</div>
        <div class="big-check">✅</div>
        <h1>eGarage – HOME LOCAL 8000</h1>
        <p class="success">Si ves esta página, el home de eGarage ya NO es Desarmaduría 2.0 🎯</p>
        <p style="color:#ff6b6b;font-weight:bold;font-size:18px;">Esta respuesta viene directamente del middleware, ANTES de llegar a las URLs.</p>
        <div class="debug-box">
            <p><strong style="color:#00ff00;">DEBUG INFO:</strong></p>
            <p>Timestamp: {timestamp}</p>
            <p>Path: {request.path}</p>
            <p>Method: {request.method}</p>
            <p>BASE_DIR: E:\\projecto\\e_garage</p>
            <p>Settings: gestion_taller.settings</p>
            <p style="color:#00ff00;font-size:20px;margin-top:20px;text-align:center;">
                ✅ ESTO ES EGARAGE, NO DESARMADURÍA 2.0
            </p>
            <p style="color:#ffff00;font-size:16px;margin-top:20px;text-align:center;">
                Este middleware intercepta la raíz "/" ANTES de que llegue a las URLs
            </p>
        </div>
    </div>
</body>
</html>"""
            response = HttpResponse(html)
            response["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response["Pragma"] = "no-cache"
            response["Expires"] = "0"
            return response
        return None



