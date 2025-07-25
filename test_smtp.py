import smtplib
from email.mime.text import MIMEText

smtp_server = 'atlantareciclajes.cl'
smtp_port = 465
username = 'subcripcion@atlantareciclajes.cl'
password = 'laila2013'  # Cambia aquí si tu contraseña es diferente

msg = MIMEText('Prueba de envío SMTP desde Python')
msg['Subject'] = 'Prueba SMTP'
msg['From'] = username
msg['To'] = username

try:
    with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
        server.login(username, password)
        server.sendmail(username, [username], msg.as_string())
    print('Correo enviado correctamente')
except Exception as e:
    print('Error al enviar correo:', e)
