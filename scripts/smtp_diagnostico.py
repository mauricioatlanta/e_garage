#!/usr/bin/env python3
import getpass
import smtplib
import ssl
from email.message import EmailMessage

import dns.resolver

HOST = "mail.atlantareciclajes.cl"
USERS = ["suscripcion@atlantareciclajes.cl", "suscripcion"]
PORTS = [465, 587, 25]
AUTH_METHODS = ["LOGIN", "PLAIN"]

print("\n=== Diagnóstico SMTP avanzado para mail.atlantareciclajes.cl ===\n")

# Mostrar comandos de diagnóstico equivalentes
print("Comandos útiles para consola:")
print(f"  openssl s_client -connect {HOST}:465 -crlf -quiet")
print(f"  openssl s_client -starttls smtp -connect {HOST}:587 -crlf -quiet")
print(
    f"  swaks --to test@dominio.com --server {HOST} --port 587 --auth LOGIN --auth-user suscripcion@atlantareciclajes.cl --tls\n"
)

# Resolver MX
print("Resolviendo MX para atlantareciclajes.cl...")
try:
    answers = dns.resolver.resolve("atlantareciclajes.cl", "MX")
    mx_hosts = [str(r.exchange).rstrip(".") for r in answers]
    print(f"  MX encontrados: {', '.join(mx_hosts)}")
    if HOST not in mx_hosts:
        print(
            f"  ⚠️  ATENCIÓN: {HOST} no es un MX directo del dominio. Puede haber relay o restricción."
        )
except Exception as e:
    print(f"  ⚠️  No se pudo resolver MX: {e}")

# Pedir credenciales
user_input = input(f"Usuario SMTP [por defecto: {USERS[0]}]: ") or USERS[0]
password = getpass.getpass("Clave SMTP: ")
from_addr = input(f"FROM (remitente) [por defecto: {USERS[0]}]: ") or USERS[0]
to_addr = input("TO (destinatario de prueba): ")
subject = "Prueba SMTP avanzada"
body = "Este es un test SMTP automático."

# Diagnóstico por puerto y método
results = []
for port in PORTS:
    for user in USERS:
        for auth_method in AUTH_METHODS:
            print(
                f"\n--- Probando puerto {port} | usuario '{user}' | AUTH {auth_method} ---"
            )
            try:
                if port == 465:
                    context = ssl.create_default_context()
                    with smtplib.SMTP_SSL(HOST, port, context=context) as server:
                        server.set_debuglevel(1)
                        cert = server.sock.getpeercert()
                        cn = cert.get("subject", ((("commonName", ""),),))[0][0][1]
                        print(f"  Certificado CN: {cn}")
                        sans = cert.get("subjectAltName", [])
                        if sans:
                            print(f"  SAN: {[x[1] for x in sans]}")
                        server.ehlo()
                        if auth_method == "LOGIN":
                            server.login(user, password)
                        else:
                            # Implementar AUTH PLAIN manualmente
                            import base64

                            authz = user
                            auth = f"\0{user}\0{password}".encode()
                            b64_auth = base64.b64encode(auth).decode("ascii")
                            code, resp = server.docmd("AUTH", "PLAIN " + b64_auth)
                            if code != 235:
                                raise smtplib.SMTPAuthenticationError(code, resp)
                        # Envío de correo
                        msg = EmailMessage()
                        msg["Subject"] = subject
                        msg["From"] = from_addr
                        msg["To"] = to_addr
                        msg.set_content(body)
                        code = server.send_message(msg)
                        print(f"  ✅ Envío exitoso. Respuesta: {code}")
                        results.append((port, user, auth_method, True, "OK"))
                else:
                    with smtplib.SMTP(HOST, port, timeout=10) as server:
                        server.set_debuglevel(1)
                        server.ehlo()
                        if port != 25 or server.has_extn("starttls"):
                            context = ssl.create_default_context()
                            server.starttls(context=context)
                            server.ehlo()
                        auths = server.esmtp_features.get("auth", "")
                        print(f"  Métodos AUTH soportados: {auths}")
                        if auth_method == "LOGIN":
                            server.login(user, password)
                        else:
                            # Implementar AUTH PLAIN manualmente
                            import base64

                            authz = user
                            auth = f"\0{user}\0{password}".encode()
                            b64_auth = base64.b64encode(auth).decode("ascii")
                            code, resp = server.docmd("AUTH", "PLAIN " + b64_auth)
                            if code != 235:
                                raise smtplib.SMTPAuthenticationError(code, resp)
                        # Envío de correo
                        msg = EmailMessage()
                        msg["Subject"] = subject
                        msg["From"] = from_addr
                        msg["To"] = to_addr
                        msg.set_content(body)
                        code = server.send_message(msg)
                        print(f"  ✅ Envío exitoso. Respuesta: {code}")
                        results.append((port, user, auth_method, True, "OK"))
            except smtplib.SMTPAuthenticationError as e:
                print(f"  ❌ Error de autenticación: {e.smtp_code} {e.smtp_error}")
                results.append(
                    (
                        port,
                        user,
                        auth_method,
                        False,
                        f"AUTH {e.smtp_code} {e.smtp_error}",
                    )
                )
            except smtplib.SMTPException as e:
                print(f"  ❌ Error SMTP: {e}")
                results.append((port, user, auth_method, False, f"SMTP {e}"))
            except ssl.SSLError as e:
                print(f"  ❌ Error SSL: {e}")
                results.append((port, user, auth_method, False, f"SSL {e}"))
            except Exception as e:
                print(f"  ❌ Error general: {e}")
                results.append((port, user, auth_method, False, f"EXC {e}"))

print("\n=== Resumen de pruebas ===")
for port, user, auth, ok, msg in results:
    status = "✅" if ok else "❌"
    print(f"{status} puerto {port} | usuario '{user}' | AUTH {auth} → {msg}")

print("\nMatriz de configuración Django lista para pegar:")
print("\n# --- SSL 465 ---")
print("EMAIL_USE_SSL=True\nEMAIL_USE_TLS=False\nEMAIL_PORT=465")
print("\n# --- STARTTLS 587 ---")
print("EMAIL_USE_SSL=False\nEMAIL_USE_TLS=True\nEMAIL_PORT=587")

print("\nNotas:")
print("- El proveedor suele requerir usuario = email completo. Prueba ambos.")
print(
    "- Si todos los métodos fallan, revisa si hay bloqueo por IP, límite de conexiones o si el buzón tiene habilitado SMTP."
)
print(
    "- Si tienes acceso al panel de control, revisa logs de acceso y errores SMTP para más detalles."
)
