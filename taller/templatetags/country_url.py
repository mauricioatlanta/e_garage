from django import template
from django.urls import reverse, NoReverseMatch

register = template.Library()

@register.simple_tag(takes_context=True)
def country_url(context, url_name, *args, **kwargs):
    request = context.get('request')
    if not request:
        return ''
    path = request.path
    # Detecta prefijo de país
    if path.startswith('/cl/'):
        ns = 'chile'
    elif path.startswith('/us/'):
        ns = 'usa'
    else:
        ns = None
    if ns:
        try:
            return reverse(f'{ns}:{url_name}', args=args, kwargs=kwargs)
        except NoReverseMatch:
            pass
    try:
        return reverse(url_name, args=args, kwargs=kwargs)
    except NoReverseMatch:
        return ''
