"""
Atajo: mismo flujo que scripts/generar_gmail_token.py usando la carpeta de este archivo.

Coloca gmail_credentials.json junto a este script y ejecuta: python generar_gmail_token.py
"""

from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

BASE_DIR = Path(__file__).resolve().parent
credentials_file = BASE_DIR / "gmail_credentials.json"
token_file = BASE_DIR / "gmail_token.json"

flow = InstalledAppFlow.from_client_secrets_file(
    str(credentials_file),
    SCOPES,
)

creds = flow.run_local_server(
    host="127.0.0.1",
    port=0,
    open_browser=True,
)

token_file.write_text(creds.to_json(), encoding="utf-8")
print(f"Token guardado en: {token_file}")
