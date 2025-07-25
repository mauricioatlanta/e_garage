# deployment_guide.py - Guía de Despliegue
"""
Script para facilitar el despliegue en producción
"""
import os
import subprocess
import sys
from pathlib import Path

def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    E-GARAGE DEPLOYMENT GUIDE                ║
║                      Versión Producción                     ║
╚══════════════════════════════════════════════════════════════╝
""")

def check_requirements():
    """Verificar requisitos del sistema"""
    print("\n🔍 VERIFICANDO REQUISITOS DEL SISTEMA...")
    
    requirements = {
        'Python': '3.8+',
        'Django': '5.1.6',
        'PostgreSQL': '12+',
        'Redis': '6+',
        'Git': 'Cualquier versión'
    }
    
    for req, version in requirements.items():
        print(f"✓ {req}: {version}")
    
    print("\n📋 REQUISITOS DE SISTEMA OPERATIVO:")
    print("• Ubuntu 20.04+ / CentOS 8+ / RHEL 8+")
    print("• 2GB RAM mínimo (4GB recomendado)")
    print("• 20GB espacio en disco")
    print("• Conexión a internet")

def setup_environment():
    """Configurar entorno de producción"""
    print("\n🛠️  CONFIGURACIÓN DEL ENTORNO...")
    
    commands = [
        "# 1. Actualizar sistema",
        "sudo apt update && sudo apt upgrade -y",
        "",
        "# 2. Instalar dependencias del sistema",
        "sudo apt install -y python3 python3-pip python3-venv",
        "sudo apt install -y postgresql postgresql-contrib",
        "sudo apt install -y redis-server",
        "sudo apt install -y nginx",
        "sudo apt install -y git curl wget",
        "",
        "# 3. Crear usuario para la aplicación",
        "sudo adduser egarage --disabled-password --gecos ''",
        "sudo usermod -aG www-data egarage",
        "",
        "# 4. Crear directorio de la aplicación",
        "sudo mkdir -p /opt/egarage",
        "sudo chown egarage:egarage /opt/egarage",
        "",
        "# 5. Configurar PostgreSQL",
        "sudo -u postgres createuser egarage",
        "sudo -u postgres createdb egarage_prod -O egarage",
        "sudo -u postgres psql -c \"ALTER USER egarage PASSWORD 'password_seguro';\"",
        "",
        "# 6. Configurar Redis",
        "sudo systemctl enable redis-server",
        "sudo systemctl start redis-server",
    ]
    
    for cmd in commands:
        print(cmd)

def deploy_application():
    """Pasos para desplegar la aplicación"""
    print("\n🚀 DESPLIEGUE DE LA APLICACIÓN...")
    
    steps = [
        "# 1. Cambiar al usuario egarage",
        "sudo su - egarage",
        "",
        "# 2. Clonar repositorio (o copiar archivos)",
        "cd /opt/egarage",
        "git clone <tu-repositorio> .",
        "# O copiar archivos: rsync -av /ruta/local/ /opt/egarage/",
        "",
        "# 3. Crear entorno virtual",
        "python3 -m venv venv",
        "source venv/bin/activate",
        "",
        "# 4. Instalar dependencias",
        "pip install --upgrade pip",
        "pip install -r requirements.txt",
        "pip install gunicorn psycopg2-binary redis whitenoise",
        "",
        "# 5. Configurar variables de entorno",
        "cp .env.example .env",
        "# Editar .env con configuración de producción",
        "",
        "# 6. Ejecutar migraciones",
        "python manage.py migrate --settings=settings_production",
        "",
        "# 7. Recopilar archivos estáticos",
        "python manage.py collectstatic --noinput --settings=settings_production",
        "",
        "# 8. Crear superusuario",
        "python manage.py createsuperuser --settings=settings_production",
    ]
    
    for step in steps:
        print(step)

def configure_services():
    """Configurar servicios del sistema"""
    print("\n⚙️  CONFIGURACIÓN DE SERVICIOS...")
    
    # Servicio Gunicorn
    gunicorn_service = """
[Unit]
Description=E-Garage Django App
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=egarage
Group=egarage
WorkingDirectory=/opt/egarage
Environment=DJANGO_SETTINGS_MODULE=settings_production
ExecStart=/opt/egarage/venv/bin/gunicorn \\
    --workers 3 \\
    --bind unix:/opt/egarage/egarage.sock \\
    --timeout 30 \\
    --keep-alive 2 \\
    --max-requests 1000 \\
    --max-requests-jitter 50 \\
    gestion_taller.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""
    
    print("📝 ARCHIVO: /etc/systemd/system/egarage.service")
    print(gunicorn_service)
    
    # Configuración Nginx
    nginx_config = """
server {
    listen 80;
    server_name tu-dominio.com www.tu-dominio.com;
    
    client_max_body_size 10M;
    
    location /static/ {
        alias /opt/egarage/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias /opt/egarage/media/;
        expires 7d;
    }
    
    location / {
        proxy_pass http://unix:/opt/egarage/egarage.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
}
"""
    
    print("\n📝 ARCHIVO: /etc/nginx/sites-available/egarage")
    print(nginx_config)
    
    print("\n🔧 COMANDOS PARA ACTIVAR SERVICIOS:")
    activation_commands = [
        "# Habilitar y iniciar E-Garage",
        "sudo systemctl daemon-reload",
        "sudo systemctl enable egarage",
        "sudo systemctl start egarage",
        "",
        "# Configurar Nginx",
        "sudo ln -s /etc/nginx/sites-available/egarage /etc/nginx/sites-enabled/",
        "sudo nginx -t",
        "sudo systemctl reload nginx",
        "",
        "# Verificar servicios",
        "sudo systemctl status egarage",
        "sudo systemctl status nginx",
    ]
    
    for cmd in activation_commands:
        print(cmd)

def setup_automation():
    """Configurar automatización (cron, monitoreo)"""
    print("\n🤖 CONFIGURACIÓN DE AUTOMATIZACIÓN...")
    
    crontab = """
# E-Garage Automation Jobs
# Backup diario a las 2:00 AM
0 2 * * * /opt/egarage/venv/bin/python /opt/egarage/backup_scheduler.py >> /var/log/egarage/backup.log 2>&1

# Monitoreo cada 15 minutos
*/15 * * * * /opt/egarage/venv/bin/python /opt/egarage/monitoring_setup.py >> /var/log/egarage/monitoring.log 2>&1

# Limpieza de logs semanalmente (domingos a las 3:00 AM)
0 3 * * 0 find /opt/egarage/logs -name "*.log" -mtime +30 -delete

# Reinicio semanal del servicio (opcional, domingos a las 4:00 AM)
0 4 * * 0 sudo systemctl restart egarage
"""
    
    print("📝 CRONTAB PARA USUARIO egarage:")
    print(crontab)
    
    print("\n🔧 COMANDOS PARA CONFIGURAR CRON:")
    cron_commands = [
        "# Crear directorio de logs",
        "sudo mkdir -p /var/log/egarage",
        "sudo chown egarage:egarage /var/log/egarage",
        "",
        "# Configurar crontab",
        "sudo -u egarage crontab -e",
        "# Pegar el contenido del crontab anterior",
    ]
    
    for cmd in cron_commands:
        print(cmd)

def security_hardening():
    """Configuración de seguridad"""
    print("\n🔒 CONFIGURACIÓN DE SEGURIDAD...")
    
    security_steps = [
        "# 1. Configurar firewall",
        "sudo ufw enable",
        "sudo ufw allow 22/tcp   # SSH",
        "sudo ufw allow 80/tcp   # HTTP",
        "sudo ufw allow 443/tcp  # HTTPS",
        "",
        "# 2. Configurar fail2ban",
        "sudo apt install fail2ban",
        "sudo systemctl enable fail2ban",
        "",
        "# 3. Configurar SSL con Let's Encrypt",
        "sudo apt install certbot python3-certbot-nginx",
        "sudo certbot --nginx -d tu-dominio.com -d www.tu-dominio.com",
        "",
        "# 4. Configurar backup de base de datos",
        "sudo -u postgres crontab -e",
        "# Agregar: 0 1 * * * pg_dump egarage_prod > /backup/db_$(date +%Y%m%d).sql",
        "",
        "# 5. Configurar logrotate",
        "sudo nano /etc/logrotate.d/egarage",
    ]
    
    for step in security_steps:
        print(step)
    
    logrotate_config = """
/var/log/egarage/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    copytruncate
}
"""
    
    print("\n📝 ARCHIVO: /etc/logrotate.d/egarage")
    print(logrotate_config)

def monitoring_services():
    """Configurar servicios de monitoreo"""
    print("\n📊 SERVICIOS DE MONITOREO RECOMENDADOS...")
    
    services = {
        "Sentry": {
            "descripción": "Monitoreo de errores en tiempo real",
            "url": "https://sentry.io",
            "configuración": "Agregar SENTRY_DSN a variables de entorno"
        },
        "UptimeRobot": {
            "descripción": "Monitoreo de disponibilidad",
            "url": "https://uptimerobot.com",
            "configuración": "Monitor HTTP cada 5 minutos"
        },
        "Google Analytics": {
            "descripción": "Análisis de uso",
            "url": "https://analytics.google.com",
            "configuración": "Agregar código de seguimiento"
        },
        "Slack/Discord": {
            "descripción": "Notificaciones de alertas",
            "url": "Webhook URL",
            "configuración": "Configurar SLACK_WEBHOOK_URL"
        }
    }
    
    for service, info in services.items():
        print(f"\n🔧 {service}:")
        print(f"   Descripción: {info['descripción']}")
        print(f"   URL: {info['url']}")
        print(f"   Configuración: {info['configuración']}")

def create_env_template():
    """Crear template de variables de entorno"""
    print("\n📄 TEMPLATE .env PARA PRODUCCIÓN...")
    
    env_template = """
# Django Settings
DJANGO_SECRET_KEY=tu-clave-super-secreta-de-produccion-de-50-caracteres
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com

# Database
DB_NAME=egarage_prod
DB_USER=egarage
DB_PASSWORD=password_super_seguro
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://127.0.0.1:6379/1

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-password-de-aplicacion

# Monitoring
SENTRY_DSN=https://tu-sentry-dsn@sentry.io/proyecto
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/tu/webhook/url
EMAIL_ALERTS=admin@tu-dominio.com,tech@tu-dominio.com

# Backup
BACKUP_RETENTION_DAYS=30
"""
    
    print(env_template)

def main():
    """Función principal"""
    print_banner()
    
    options = {
        '1': ('Verificar Requisitos', check_requirements),
        '2': ('Configurar Entorno', setup_environment),
        '3': ('Desplegar Aplicación', deploy_application),
        '4': ('Configurar Servicios', configure_services),
        '5': ('Configurar Automatización', setup_automation),
        '6': ('Seguridad y Hardening', security_hardening),
        '7': ('Servicios de Monitoreo', monitoring_services),
        '8': ('Template Variables .env', create_env_template),
        '9': ('Guía Completa', lambda: [func() for _, func in options.values() if func != options['9'][1]]),
        '0': ('Salir', lambda: sys.exit(0))
    }
    
    while True:
        print("\n" + "="*60)
        print("SELECCIONA UNA OPCIÓN:")
        print("="*60)
        
        for key, (description, _) in options.items():
            print(f"{key}. {description}")
        
        choice = input("\nIngresa tu opción (0-9): ").strip()
        
        if choice in options:
            _, func = options[choice]
            try:
                func()
            except KeyboardInterrupt:
                print("\n\nOperación cancelada.")
            except Exception as e:
                print(f"\nError: {e}")
        else:
            print("Opción inválida. Intenta de nuevo.")

if __name__ == "__main__":
    main()
