import logging

from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver

from taller.models.empresa import Empresa
from taller.models.team_member import TeamMember

log = logging.getLogger(__name__)


@receiver(post_save, sender=Empresa)
def ensure_owner_rbac(sender, instance, **kwargs):
    """
    Garantiza que el owner lógico (Empresa.user) quede sincronizado con RBAC:
    - Grupo Django Owner
    - TeamMember activo con rol Owner
    """
    user = getattr(instance, "user", None)
    if not user_id := getattr(instance, "user_id", None):
        return

    owner_group, _ = Group.objects.get_or_create(name="Owner")
    if not user.groups.filter(name="Owner").exists():
        user.groups.add(owner_group)
        log.info(
            "[RBAC_SYNC] Grupo Owner asignado a user_id=%s empresa_id=%s",
            user.id,
            instance.id,
        )

    tm, created = TeamMember.objects.get_or_create(
        user=user,
        empresa=instance,
        defaults={"rol": "Owner", "is_active": True},
    )

    changed = False
    update_fields = []

    if tm.rol != "Owner":
        tm.rol = "Owner"
        changed = True
        update_fields.append("rol")

    if not tm.is_active:
        tm.is_active = True
        changed = True
        update_fields.append("is_active")

    if changed:
        tm.save(update_fields=update_fields)

    if created:
        log.info(
            "[RBAC_SYNC] TeamMember Owner creado para user_id=%s empresa_id=%s",
            user.id,
            instance.id,
        )
