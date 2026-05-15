"""
Comando de gestión para crear los grupos de roles estándar de eGarage

Ejecutar: python manage.py setup_roles
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = "Crea los grupos de roles estándar para eGarage con sus permisos"

    def handle(self, *args, **options):
        """
        Crea los grupos de roles estándar:
        - Owner (Dueño): Acceso total
        - Admin (Administrador): Gestión operativa
        - Vendedor (Sales): Crear cotizaciones, vender
        - Tecnico (Tech): Solo sus OTs asignadas
        """

        # Definir roles y sus permisos asociados
        # Nota: Los permisos son opcionales, principalmente usamos grupos
        roles_def = {
            "Owner": {
                "description": "Dueño - Acceso total (Configuración, BI, Usuarios)",
                "permissions": [
                    # Dashboard BI
                    "view_dashboard_bi",
                    # Configuración
                    "change_configuracion",
                    "view_configuracion",
                    # Usuarios
                    "add_user",
                    "change_user",
                    "delete_user",
                    "view_user",
                    # Documentos
                    "add_documento",
                    "change_documento",
                    "delete_documento",
                    "view_documento",
                    # Inventario
                    "change_repuesto",
                    "view_repuesto",
                    # Anular facturas
                    "anular_documento",
                ],
            },
            "Admin": {
                "description": "Administrador - Gestión operativa (Inventario, Anular facturas), sin configuración sensible",
                "permissions": [
                    # Dashboard BI (solo lectura)
                    "view_dashboard_bi",
                    # Documentos (gestión operativa)
                    "add_documento",
                    "change_documento",
                    "delete_documento",
                    "view_documento",
                    # Anular facturas
                    "anular_documento",
                    # Inventario
                    "change_repuesto",
                    "view_repuesto",
                    # Clientes y vehículos
                    "view_cliente",
                    "change_cliente",
                    "view_vehiculo",
                    "change_vehiculo",
                ],
            },
            "Vendedor": {
                "description": "Vendedor - Crear cotizaciones, vender, ver clientes. No puede borrar ni ver BI",
                "permissions": [
                    # Documentos (crear y ver, no borrar)
                    "add_documento",
                    "change_documento",
                    "view_documento",
                    # Clientes y vehículos
                    "view_cliente",
                    "change_cliente",
                    "add_cliente",
                    "view_vehiculo",
                    "change_vehiculo",
                    "add_vehiculo",
                    # Repuestos (solo ver)
                    "view_repuesto",
                ],
            },
            "Tecnico": {
                "description": "Técnico - Solo ve sus Órdenes de Trabajo asignadas. No ve precios de compra ni ganancias",
                "permissions": [
                    # Documentos (solo sus OTs asignadas)
                    "view_documento",
                    "change_documento",  # Para actualizar estado de sus OTs
                    # Clientes y vehículos (solo ver)
                    "view_cliente",
                    "view_vehiculo",
                    # Repuestos (solo ver, sin precios de compra)
                    "view_repuesto",
                ],
            },
        }

        created_count = 0
        updated_count = 0

        for role_name, role_config in roles_def.items():
            # Crear o obtener el grupo
            group, created = Group.objects.get_or_create(name=role_name)

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Rol creado: {role_name} - {role_config["description"]}')
                )
                created_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️  Rol ya existe: {role_name} - {role_config["description"]}'
                    )
                )
                updated_count += 1

            # Intentar asignar permisos si están definidos
            # Nota: Esto es opcional, principalmente usamos la pertenencia al grupo
            permissions_to_assign = []

            for perm_codename in role_config.get("permissions", []):
                # Intentar encontrar el permiso
                # Formato: <app_label>.<codename>
                try:
                    if "." in perm_codename:
                        app_label, codename = perm_codename.split(".", 1)
                        perm = Permission.objects.get(
                            content_type__app_label=app_label, codename=codename
                        )
                        permissions_to_assign.append(perm)
                    else:
                        # Buscar en cualquier app
                        perm = Permission.objects.filter(codename=perm_codename).first()
                        if perm:
                            permissions_to_assign.append(perm)
                except Permission.DoesNotExist:
                    # Si no existe el permiso, lo ignoramos (no crítico)
                    pass

            # Asignar permisos al grupo
            if permissions_to_assign:
                group.permissions.set(permissions_to_assign)
                self.stdout.write(
                    f"   📋 Asignados {len(permissions_to_assign)} permisos a {role_name}"
                )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Proceso completado: {created_count} roles creados, "
                f"{updated_count} roles actualizados"
            )
        )
        self.stdout.write("")
        self.stdout.write("Roles disponibles:")
        for role_name in roles_def.keys():
            count = Group.objects.filter(name=role_name).count()
            if count > 0:
                group = Group.objects.get(name=role_name)
                user_count = group.user_set.count()
                self.stdout.write(f"  - {role_name}: {user_count} usuario(s) asignado(s)")
