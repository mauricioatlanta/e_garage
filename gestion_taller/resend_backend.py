import resend
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings

class ResendBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        
        resend.api_key = "re_ayHbTkv4_F3rhviV1ewsWBhBH2Cm8dgNp"
        sent_count = 0
        
        for message in email_messages:
            try:
                # Extraer el contenido HTML si existe, si no, usar el body
                html_content = ""
                if hasattr(message, 'alternatives') and message.alternatives:
                    for alt in message.alternatives:
                        if alt[1] == "text/html":
                            html_content = alt[0]
                            break
                
                if not html_content:
                    html_content = f"<p>{message.body}</p>".replace("\n", "<br>")

                params = {
                    "from": getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@egarage.cl'),
                    "to": message.to,
                    "subject": message.subject,
                    "html": html_content,
                }
                resend.Emails.send(params)
                sent_count += 1
            except Exception as e:
                # Esto saldrá en los logs de gunicorn
                print(f"DEBUG RESEND ERROR: {e}")
        return sent_count
