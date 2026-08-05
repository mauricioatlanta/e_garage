"""
Mark stale sessions as inactive.

Run periodically via cron (every 5–15 minutes is sufficient):

    */10 * * * * /path/to/venv/bin/python /path/to/manage.py trust_cleanup

Or via a task scheduler (Celery Beat, APScheduler) when available.

What it does:
  - Sets activa=False on SesionUsuario rows whose ultima_actividad
    is older than INACTIVITY_MINUTES (default 30).
  - Does NOT delete rows — historical data is preserved for Phase 3 analytics.
"""

from django.core.management.base import BaseCommand

from taller.utils.trust import INACTIVITY_MINUTES, mark_inactive_sessions


class Command(BaseCommand):
    help = (
        f"Mark sessions inactive after {INACTIVITY_MINUTES} min of inactivity "
        "(Trust & Security Phase 1)"
    )

    def handle(self, *args, **options):
        updated = mark_inactive_sessions()
        self.stdout.write(
            self.style.SUCCESS(f"trust_cleanup: {updated} sesiones marcadas como inactivas.")
        )
