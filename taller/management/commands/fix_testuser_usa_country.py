from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from taller.models import Empresa
from django.db import transaction


class Command(BaseCommand):
    help = 'Cambiar el país del usuario testuser_usa a US de forma definitiva'

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                user = User.objects.get(username='testuser_usa')
                self.stdout.write(f'Usuario encontrado: {user.username}')
                
                # Buscar TODAS las empresas relacionadas
                empresas_user = Empresa.objects.filter(user=user)
                empresas_usuario = Empresa.objects.filter(usuario=user)
                
                self.stdout.write(f'Empresas con campo user: {empresas_user.count()}')
                for empresa in empresas_user:
                    self.stdout.write(f'  ANTES: {empresa.nombre_taller} -> {empresa.pais}')
                    empresa.pais = 'US'
                    empresa.save()
                    empresa.refresh_from_db()
                    self.stdout.write(f'  DESPUÉS: {empresa.nombre_taller} -> {empresa.pais}')
                
                self.stdout.write(f'Empresas con campo usuario: {empresas_usuario.count()}')
                for empresa in empresas_usuario:
                    self.stdout.write(f'  ANTES: {empresa.nombre_taller} -> {empresa.pais}')
                    empresa.pais = 'US'
                    empresa.save()
                    empresa.refresh_from_db()
                    self.stdout.write(f'  DESPUÉS: {empresa.nombre_taller} -> {empresa.pais}')
                
                # Verificación final
                self.stdout.write('\n=== VERIFICACIÓN FINAL ===')
                all_empresas = Empresa.objects.filter(user=user) | Empresa.objects.filter(usuario=user)
                for empresa in all_empresas:
                    self.stdout.write(f'Empresa: {empresa.nombre_taller} -> País: {empresa.pais}')
                
                if all_empresas.filter(pais='US').count() > 0:
                    self.stdout.write(
                        self.style.SUCCESS('✅ ¡Cambio completado! Al menos una empresa tiene país US')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR('❌ No se pudo cambiar el país a US')
                    )
                    
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Usuario testuser_usa no existe')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {e}')
            )
