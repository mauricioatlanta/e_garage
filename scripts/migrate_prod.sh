#!/usr/bin/env bash
# Ejecuta migrate (y asegura Site id=1) con el mismo entorno que Gunicorn en producción.
# Uso en el servidor:
#   cd /srv/egarage && bash scripts/migrate_prod.sh
#
# Requiere: .env.prod en el directorio del proyecto con al menos DJANGO_SECRET_KEY (o SECRET_KEY).

set -e
cd "$(dirname "$0")/.."

if [ ! -f .env.prod ]; then
  echo "No se encontró .env.prod. Cópialo al servidor o define las variables a mano."
  exit 1
fi

# Cargar .env.prod sin usar source (evita CRLF y comentarios como comandos)
while IFS= read -r line || [ -n "$line" ]; do
  line="${line//$'\r'/}"        # quitar CRLF
  line="${line%%[[:space:]]}"   # quitar espacios finales
  [ -z "$line" ] && continue
  case "$line" in \#*) continue ;; esac
  export "$line"
done < .env.prod

export DJANGO_SETTINGS_MODULE=gestion_taller.settings_prod

echo "Migrando con DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE ..."
python manage.py migrate

echo "Asegurando Site id=1 (egarage.cl) ..."
python manage.py shell -c "
from django.contrib.sites.models import Site
s, _ = Site.objects.get_or_create(id=1, defaults={'domain': 'egarage.cl', 'name': 'eGarage'})
if s.domain != 'egarage.cl':
    s.domain, s.name = 'egarage.cl', 'eGarage'
    s.save()
print('Site:', s.domain)
"

echo "Listo. Reinicia gunicorn si hace falta: sudo systemctl restart gunicorn"
