from django.core.management.base import BaseCommand
from django.test import Client
from django.test.utils import override_settings


class Command(BaseCommand):
    help = "Smoke test rapido de rutas VE usando HTTPS y follow redirects"

    def handle(self, *args, **options):
        client = Client(HTTP_HOST="egarage.cl")

        checks = [
            ("/ve/es/", {200, 301, 302}),
            ("/ve/es/bienvenida/", {200, 301, 302}),
            ("/ve/es/accounts/login/", {200, 301, 302}),
            ("/ve/es/clientes/", {200, 301, 302}),
            ("/ve/es/vehiculos/", {200, 301, 302}),
            ("/ve/es/documentos/", {200, 301, 302}),
            ("/ve/es/documentos/form/", {200, 301, 302}),
            ("/ve/es/documentos/lista/", {200, 301, 302}),
            ("/ve/es/desarme/", {200, 301, 302}),
            ("/ve/es/desarme/vehiculos/", {200, 301, 302}),
            ("/ve/es/reportes/", {200, 301, 302}),
            ("/ve/es/reportes/dashboard-inteligencia-operativa/", {200, 301, 302}),
            ("/ve/es/api/status/", {200, 301, 302}),
            ("/ve/es/ajax/clientes/buscar/", {200, 301, 302}),
        ]

        failures = 0
        self.stdout.write(self.style.SUCCESS("== Smoke VE rutas (HTTPS + redirects) =="))

        with override_settings(
            ALLOWED_HOSTS=[
                "egarage.cl",
                "www.egarage.cl",
                "127.0.0.1",
                "localhost",
                "testserver",
            ]
        ):
            for path, expected in checks:
                response = client.get(path, secure=True, follow=True)
                final_code = response.status_code
                redirect_chain = response.redirect_chain
                final_url = redirect_chain[-1][0] if redirect_chain else path

                if final_code in expected:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"OK {path} -> {final_code} ({len(redirect_chain)} redirects) -> {final_url}"
                        )
                    )
                else:
                    failures += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f"FAIL {path} -> {final_code} ({len(redirect_chain)} redirects) -> {final_url}"
                        )
                    )

        if failures:
            raise SystemExit(1)

        self.stdout.write(self.style.SUCCESS("Smoke VE completado sin fallas."))
