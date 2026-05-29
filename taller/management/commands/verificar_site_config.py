"""
Comando para verificar y corregir la configuración del Site de Django.
Esto es crítico para que los correos de password reset funcionen correctamente.
"""
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.conf import settings


class Command(BaseCommand):
    help = "Verifica y corrige la configuración del Site de Django para password reset"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🔍 Verificando configuración del Site..."))
        
        try:
            site = Site.objects.get_current()
            expected_domain = getattr(settings, "SITE_DOMAIN", "egarage.cl")
            expected_name = getattr(settings, "SITE_NAME", "eGarage")
            site_id = getattr(settings, "SITE_ID", 1)
            
            self.stdout.write(f"  Site ID: {site.id}")
            self.stdout.write(f"  Site Domain actual: {site.domain}")
            self.stdout.write(f"  Site Name actual: {site.name}")
            self.stdout.write(f"  Domain esperado: {expected_domain}")
            self.stdout.write(f"  Name esperado: {expected_name}")
            self.stdout.write(f"  SITE_ID configurado: {site_id}")
            
            needs_update = False
            
            if site.domain != expected_domain:
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⚠️  El dominio del Site ({site.domain}) no coincide con "
                        f"el configurado en settings ({expected_domain})"
                    )
                )
                needs_update = True
            
            if site.name != expected_name:
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⚠️  El nombre del Site ({site.name}) no coincide con "
                        f"el configurado en settings ({expected_name})"
                    )
                )
                needs_update = True
            
            if site.id != site_id:
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⚠️  El ID del Site ({site.id}) no coincide con "
                        f"SITE_ID en settings ({site_id})"
                    )
                )
            
            if needs_update:
                self.stdout.write(self.style.SUCCESS("  🔧 Actualizando Site..."))
                site.domain = expected_domain
                site.name = expected_name
                site.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✅ Site actualizado: domain={site.domain}, name={site.name}"
                    )
                )
            else:
                self.stdout.write(self.style.SUCCESS("  ✅ La configuración del Site es correcta"))
            
            # Verificar configuración de email
            self.stdout.write("\n📧 Verificando configuración de email...")
            email_host = getattr(settings, "EMAIL_HOST", None)
            email_user = getattr(settings, "EMAIL_HOST_USER", None)
            email_password = getattr(settings, "EMAIL_HOST_PASSWORD", None)
            
            if email_host:
                self.stdout.write(f"  EMAIL_HOST: {email_host}")
            else:
                self.stdout.write(self.style.ERROR("  ❌ EMAIL_HOST no configurado"))
            
            if email_user:
                self.stdout.write(f"  EMAIL_HOST_USER: {email_user}")
            else:
                self.stdout.write(self.style.ERROR("  ❌ EMAIL_HOST_USER no configurado"))
            
            if email_password:
                self.stdout.write("  EMAIL_HOST_PASSWORD: ✅ Configurado")
            else:
                self.stdout.write(self.style.ERROR("  ❌ EMAIL_HOST_PASSWORD no configurado"))
            
            default_from = getattr(settings, "DEFAULT_FROM_EMAIL", None)
            if default_from:
                self.stdout.write(f"  DEFAULT_FROM_EMAIL: {default_from}")
            
            self.stdout.write(
                self.style.SUCCESS("\n✅ Verificación completada. Si hay problemas, revisa los mensajes arriba.")
            )
            
        except Site.DoesNotExist:
            self.stdout.write(self.style.ERROR("  ❌ No se encontró el Site con ID configurado"))
            self.stdout.write("  🔧 Creando Site...")
            site = Site.objects.create(
                id=getattr(settings, "SITE_ID", 1),
                domain=getattr(settings, "SITE_DOMAIN", "egarage.cl"),
                name=getattr(settings, "SITE_NAME", "eGarage"),
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"  ✅ Site creado: domain={site.domain}, name={site.name}"
                )
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ❌ Error: {e}"))









