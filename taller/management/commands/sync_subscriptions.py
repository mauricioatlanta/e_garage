from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from taller.models.empresa import Empresa


class Command(BaseCommand):
    """
    Comando para sincronizar el estado de las suscripciones.

    Este comando verifica todas las empresas y actualiza:
    - suscripcion_activa: False si fecha_fin < now
    - notificacion_vencido: True si fecha_fin < now
    - notificacion_5_dias: True si faltan exactamente 5 días
    - notificacion_1_dia: True si falta exactamente 1 día

    IMPORTANTE: Este comando NO envía notificaciones, solo sincroniza el estado.
    Para enviar notificaciones, usar el comando 'notificar_vencimientos'.

    Uso:
        python manage.py sync_subscriptions          # Ejecución normal
        python manage.py sync_subscriptions --dry-run  # Modo prueba (no actualiza)

    Ejecutar diariamente con cron (recomendado: cada noche a las 2:00 AM):
        0 2 * * * cd /ruta/proyecto && python manage.py sync_subscriptions

    O con systemd timer (ver sync_subscriptions.timer en scripts/)
    """

    help = "Sincroniza el estado de las suscripciones y marca notificaciones"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Ejecutar en modo de prueba sin actualizar la base de datos",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)

        if dry_run:
            self.stdout.write(
                self.style.WARNING("[DRY-RUN] Modo de prueba: No se actualizará la base de datos")
            )

        self.stdout.write("[INFO] Iniciando sincronización de suscripciones...")

        now = timezone.now()
        hoy = now.date()

        # Obtener todas las empresas con fecha_fin definida
        empresas = Empresa.objects.filter(fecha_fin__isnull=False).select_related("user")

        stats = {
            "vencidas": 0,
            "5_dias": 0,
            "1_dia": 0,
            "reactivadas": 0,  # Si se detecta que una suscripción vencida fue renovada
            "sin_cambios": 0,
        }

        for empresa in empresas:
            fecha_fin_date = empresa.fecha_fin.date() if empresa.fecha_fin else None
            if not fecha_fin_date:
                continue

            dias_restantes = (fecha_fin_date - hoy).days
            cambios = []

            # 1. Verificar si está vencida
            if fecha_fin_date < hoy:
                # Suscripción vencida
                if empresa.suscripcion_activa:
                    cambios.append("suscripcion_activa=False")
                    if not dry_run:
                        empresa.suscripcion_activa = False
                    stats["vencidas"] += 1

                if not empresa.notificacion_vencido:
                    cambios.append("notificacion_vencido=True")
                    if not dry_run:
                        empresa.notificacion_vencido = True
                    stats["vencidas"] += 1

            # 2. Verificar si faltan exactamente 5 días
            elif dias_restantes == 5:
                if not empresa.notificacion_5_dias:
                    cambios.append("notificacion_5_dias=True")
                    if not dry_run:
                        empresa.notificacion_5_dias = True
                    stats["5_dias"] += 1

            # 3. Verificar si falta exactamente 1 día
            elif dias_restantes == 1:
                if not empresa.notificacion_1_dia:
                    cambios.append("notificacion_1_dia=True")
                    if not dry_run:
                        empresa.notificacion_1_dia = True
                    stats["1_dia"] += 1

            # 4. Verificar si una suscripción que estaba vencida fue renovada
            elif empresa.fecha_fin > now and not empresa.suscripcion_activa:
                # Suscripción futura pero marcada como inactiva (posible renovación)
                if not dry_run:
                    empresa.suscripcion_activa = True
                    # Resetear notificaciones cuando se renueva
                    empresa.notificacion_vencido = False
                cambios.append("suscripcion_activa=True (reactivada)")
                stats["reactivadas"] += 1

            # Guardar cambios si hay alguno
            if cambios:
                if not dry_run:
                    empresa.save(
                        update_fields=[
                            "suscripcion_activa",
                            "notificacion_vencido",
                            "notificacion_5_dias",
                            "notificacion_1_dia",
                        ]
                    )

                self.stdout.write(
                    self.style.SUCCESS(
                        f"[OK] {empresa.nombre_taller} ({empresa.user.email}): "
                        f"{', '.join(cambios)} - {dias_restantes} días restantes"
                    )
                )
            else:
                stats["sin_cambios"] += 1

        # Mostrar resumen
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("[RESUMEN DE SINCRONIZACIÓN]"))
        self.stdout.write(f"  Suscripciones vencidas actualizadas: {stats['vencidas']}")
        self.stdout.write(f"  Notificaciones de 5 días marcadas: {stats['5_dias']}")
        self.stdout.write(f"  Notificaciones de 1 día marcadas: {stats['1_dia']}")
        self.stdout.write(f"  Suscripciones reactivadas: {stats['reactivadas']}")
        self.stdout.write(f"  Sin cambios: {stats['sin_cambios']}")
        self.stdout.write("=" * 60)

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "\n[DRY-RUN] Los cambios mostrados no fueron guardados. "
                    "Ejecuta sin --dry-run para aplicar cambios."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n[OK] Sincronización completada. Total procesado: {empresas.count()}"
                )
            )
