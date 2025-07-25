import smtplib
from email.mime.text import MIMEText

# Cambia aquí por la contraseña actualizada de cPanel
EMAIL_HOST = 'mail.atlantareciclajes.cl'
EMAIL_PORT = 465
EMAIL_HOST_USER = 'subcripcion@atlantareciclajes.cl'
EMAIL_HOST_PASSWORD = 'Laila2024@@'  # ← pon aquí la nueva contraseña

FROM = 'subcripcion@atlantareciclajes.cl'
TO = 'tu_correo_destino@dominio.com'  # Cambia por tu correo real para probar

msg = MIMEText('¡Prueba SMTP exitosa desde Python!')
msg['Subject'] = 'Prueba SMTP CPanel'
msg['From'] = FROM
msg['To'] = TO

try:
    with smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT) as server:
        server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
        server.sendmail(FROM, [TO], msg.as_string())
    print('✅ Correo enviado correctamente.')
except Exception as e:
    print('❌ Error al enviar correo:', e)
