from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


class Command(BaseCommand):
    help = (
        "Genera gmail_token.json con OAuth (app de escritorio / localhost). "
        "Solo tiene sentido en la misma máquina donde abres el navegador; "
        "en servidor remoto por SSH usa scripts/generar_gmail_token.py en tu PC y sube el token."
    )

    def handle(self, *args, **options):
        credentials_file = getattr(settings, "GMAIL_CREDENTIALS_FILE", None)
        token_file = getattr(settings, "GMAIL_TOKEN_FILE", None)

        if not credentials_file:
            raise RuntimeError("Falta GMAIL_CREDENTIALS_FILE en settings.")
        if not token_file:
            raise RuntimeError("Falta GMAIL_TOKEN_FILE en settings.")

        credentials_path = Path(credentials_file)
        token_path = Path(token_file)

        if not credentials_path.exists():
            raise RuntimeError(f"No existe credentials file: {credentials_path}")

        flow = InstalledAppFlow.from_client_secrets_file(
            str(credentials_path),
            SCOPES,
        )
        # run_console() fue retirado en versiones recientes; localhost debe coincidir con redirect del JSON.
        creds = flow.run_local_server(
            host="127.0.0.1",
            port=0,
            open_browser=True,
        )

        token_path.write_text(creds.to_json(), encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Token guardado en {token_path}"))
