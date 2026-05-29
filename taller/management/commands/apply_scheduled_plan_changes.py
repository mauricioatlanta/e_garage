from django.core.management.base import BaseCommand

from taller.services.plan_change_service import (
    apply_due_scheduled_changes,
    expire_pending_upgrades,
    get_plan_change_health,
)


class Command(BaseCommand):
    help = "Aplica downgrades programados y expira upgrades pendientes sin pago."

    def handle(self, *args, **options):
        applied_stats = apply_due_scheduled_changes()
        expired_stats = expire_pending_upgrades()
        health = get_plan_change_health()
        self.stdout.write(
            self.style.SUCCESS(
                "Cambios aplicados: "
                f"{applied_stats['applied']}. "
                f"Cambios fallidos: {applied_stats['failed']}. "
                f"Upgrades expirados: {expired_stats['expired']}."
            )
        )
        self.stdout.write(
            "Health billing: "
            f"pending_upgrades={health['pending_upgrades']} "
            f"expired_pending_upgrades={health['expired_pending_upgrades']} "
            f"scheduled_downgrades={health['scheduled_downgrades']} "
            f"failed_downgrades={health['failed_downgrades']}"
        )
