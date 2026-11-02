from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from django.utils import timezone


@dataclass(frozen=True)
class SuscripcionInfo:
    estado: str
    motivo: str
    dias_restantes: int
    fecha_expiracion: object
    plan: str
    suscripcion_activa: bool


def _get_empresa_fecha_expiracion(empresa):
    if not empresa:
        return None
    try:
        return empresa.fecha_expiracion
    except Exception:
        return None


def _get_dias_restantes(empresa) -> int:
    if not empresa:
        return 0
    try:
        return int(getattr(empresa, "dias_restantes", 0) or 0)
    except Exception:
        return 0


def get_suscripcion_activa(empresa) -> Optional[SuscripcionInfo]:
    if not empresa:
        return None

    now = timezone.now()
    fecha_expiracion = _get_empresa_fecha_expiracion(empresa)
    dias_restantes = _get_dias_restantes(empresa)

    plan = getattr(empresa, "plan", None) or "trial"
    suscripcion_activa = bool(getattr(empresa, "suscripcion_activa", True))

    if not fecha_expiracion:
        return SuscripcionInfo(
            estado="sin_suscripcion",
            motivo="empresa_sin_fecha_expiracion",
            dias_restantes=0,
            fecha_expiracion=None,
            plan=plan,
            suscripcion_activa=suscripcion_activa,
        )

    expiro = now > fecha_expiracion

    if expiro and not suscripcion_activa:
        return SuscripcionInfo(
            estado="vencida",
            motivo="suscripcion_vencida",
            dias_restantes=0,
            fecha_expiracion=fecha_expiracion,
            plan=plan,
            suscripcion_activa=suscripcion_activa,
        )

    if not suscripcion_activa:
        return SuscripcionInfo(
            estado="inactiva",
            motivo="suscripcion_inactiva",
            dias_restantes=max(dias_restantes, 0),
            fecha_expiracion=fecha_expiracion,
            plan=plan,
            suscripcion_activa=suscripcion_activa,
        )

    if str(plan).lower() == "trial":
        if expiro:
            return SuscripcionInfo(
                estado="trial_expirado",
                motivo="trial_expirado",
                dias_restantes=0,
                fecha_expiracion=fecha_expiracion,
                plan=plan,
                suscripcion_activa=suscripcion_activa,
            )
        return SuscripcionInfo(
            estado="trial_activo",
            motivo="trial_activo",
            dias_restantes=max(dias_restantes, 0),
            fecha_expiracion=fecha_expiracion,
            plan=plan,
            suscripcion_activa=suscripcion_activa,
        )

    if expiro:
        return SuscripcionInfo(
            estado="vencida_activa",
            motivo="vencida_pero_flag_activo",
            dias_restantes=0,
            fecha_expiracion=fecha_expiracion,
            plan=plan,
            suscripcion_activa=suscripcion_activa,
        )

    return SuscripcionInfo(
        estado="activa",
        motivo="suscripcion_activa",
        dias_restantes=max(dias_restantes, 0),
        fecha_expiracion=fecha_expiracion,
        plan=plan,
        suscripcion_activa=suscripcion_activa,
    )


def empresa_tiene_acceso(empresa) -> bool:
    if not empresa:
        return False

    info = get_suscripcion_activa(empresa)
    if not info:
        return False

    # Mantener compatibilidad con el comportamiento actual en producción
    # (bloqueo efectivo = empresa.debe_bloquear).
    try:
        return not bool(getattr(empresa, "debe_bloquear", False))
    except Exception:
        return info.estado in ("activa", "trial_activo")


def motivo_bloqueo_suscripcion(empresa) -> str:
    if not empresa:
        return "sin_empresa"

    info = get_suscripcion_activa(empresa)
    if not info:
        return "sin_suscripcion"

    if empresa_tiene_acceso(empresa):
        return ""

    return info.estado
