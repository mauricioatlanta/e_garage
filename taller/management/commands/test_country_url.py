#!/usr/bin/env python
"""
Comando Django para probar el tag country_url.
"""
from django.core.management.base import BaseCommand
from django.template import Context, Template
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser


class Command(BaseCommand):
    help = 'Prueba el tag country_url para configuracion_tecnicos'

    def handle(self, *args, **options):
        self.stdout.write('🔍 Probando tag country_url...')
        
        # Crear un request simulado para US
        factory = RequestFactory()
        request = factory.get('/us/')
        request.user = AnonymousUser()
        
        # Simular contexto de país
        request.country = 'US'
        
        # Crear contexto de template
        context = Context({
            'request': request,
            'country': 'US',
        })
        
        # Probar el tag country_url
        template_string = """
        {% load country_url %}
        {% country_url 'configuracion_tecnicos' app_namespace='direct' as url_config_tecnicos %}
        URL generada: {{ url_config_tecnicos }}
        """
        
        template = Template(template_string)
        rendered = template.render(context)
        
        self.stdout.write(f'📝 Resultado: {rendered.strip()}')
        
        # Verificar si la URL es correcta
        if 'configuracion_tecnicos' in rendered and '/taller/' not in rendered:
            self.stdout.write(self.style.SUCCESS('✅ Tag country_url funciona correctamente'))
        else:
            self.stdout.write(self.style.ERROR('❌ Tag country_url no funciona correctamente'))
            
        self.stdout.write('✅ Prueba completada.')
