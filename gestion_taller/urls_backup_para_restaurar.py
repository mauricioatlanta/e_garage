from django.contrib import admin
from django.http import HttpResponse
from django.urls import path


def home(request):
    return HttpResponse(
        """
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>EGARAGE SUPER TEST</title>
        </head>
        <body style="background:#020617;color:#e5e7eb;font-family:system-ui;padding:40px">
            <h1 style="font-size:40px;color:#22c55e">
                ✅ eGarage SUPER TEST – PUERTO 8000
            </h1>
            <p>Si ves esto, NO hay forma de que sea la landing de Desarmaduría 2.0.</p>
        </body>
        </html>
    """
    )


urlpatterns = [
    path("", home, name="home"),
    path("admin/", admin.site.urls),
]
