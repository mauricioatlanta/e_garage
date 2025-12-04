# Instrucciones para Reactivar Starfield.js

Si starfield.js NO es el culpable del scroll, descomenta estas líneas en `templates/base.html`:

## Busca (línea ~679):
```django
{# TEMP: desactivar starfield para probar scroll en móviles #}
{# {% if enable_space_bg|default:1 and enable_space_bg != 2 %}
    <script src="{% static 'js/starfield.js' %}"></script>
{% endif %} #}
```

## Reemplaza por:
```django
{# --- Starfield JS reactivado --- #}
{% if enable_space_bg|default:1 and enable_space_bg != 2 %}
  <script src="{% static 'js/starfield.js' %}"></script>
{% endif %}
```

## Guarda y reinicia el servidor:
```bash
python manage.py runserver
```


