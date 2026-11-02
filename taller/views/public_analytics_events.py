from django.http import JsonResponse
from django.views.decorators.http import require_POST

from taller.services.abandoned_lead_service import capture_abandoned_lead
from taller.services.public_event_tracking import (
    PublicEventValidationError,
    check_public_event_rate_limit,
    get_session_from_request_cookie,
    parse_public_event_payload,
    record_public_event,
    validate_public_event_payload,
)
from taller.services.public_attribution import attach_public_analytics_cookies, get_or_create_public_session
from taller.services.public_traffic_classifier import is_allowed_public_analytics_host, is_scanner_path, normalize_host


@require_POST
def public_analytics_event(request):
    host = normalize_host(request.get_host())
    user = getattr(request, "user", None)
    if (
        not is_allowed_public_analytics_host(host)
        or is_scanner_path(request.path)
        or (user is not None and getattr(user, "is_staff", False))
    ):
        return JsonResponse({"ok": True, "created": False, "ignored": True})
    session = get_session_from_request_cookie(request)
    if session is None:
        session = get_or_create_public_session(request, page_type="event")
    if (
        session is not None and session.is_internal
    ):
        return attach_public_analytics_cookies(request, JsonResponse({"ok": True, "created": False, "ignored": True}))
    if session is None:
        return JsonResponse({"ok": False, "error": "session_unavailable"}, status=503)

    allowed, retry_after = check_public_event_rate_limit(
        request,
        session.anonymous_session_hash,
    )
    if not allowed:
        response = JsonResponse(
            {"ok": False, "error": "rate_limit_exceeded", "retry_after": retry_after},
            status=429,
        )
        response["Retry-After"] = str(retry_after)
        return attach_public_analytics_cookies(request, response)

    try:
        payload = parse_public_event_payload(request)
        event_type, path, dedupe_key, metadata = validate_public_event_payload(payload)
    except PublicEventValidationError as exc:
        return attach_public_analytics_cookies(request, JsonResponse({"ok": False, "error": exc.code}, status=exc.status))

    if session.is_bot or session.is_internal:
        return attach_public_analytics_cookies(request, JsonResponse({"ok": True, "created": False, "ignored": True}))

    event, created = record_public_event(
        session=session,
        event_type=event_type,
        path=path,
        dedupe_key=dedupe_key,
        metadata=metadata,
    )
    return attach_public_analytics_cookies(request, JsonResponse({"ok": True, "created": created, "event_id": event.pk}))


@require_POST
def public_signup_lead(request):
    try:
        payload = parse_public_event_payload_for_lead(request)
    except PublicEventValidationError as exc:
        return JsonResponse({"ok": False, "error": exc.code}, status=exc.status)

    lead, created = capture_abandoned_lead(request, payload)
    return JsonResponse({"ok": True, "created": created, "lead_id": getattr(lead, "pk", None)})


def parse_public_event_payload_for_lead(request) -> dict:
    if request.content_type != "application/json":
        raise PublicEventValidationError("unsupported_media_type", status=415)
    if len(request.body or b"") > 4096:
        raise PublicEventValidationError("payload_too_large", status=413)
    try:
        import json

        payload = json.loads((request.body or b"{}").decode("utf-8"))
    except Exception:
        raise PublicEventValidationError("invalid_json")
    if not isinstance(payload, dict):
        raise PublicEventValidationError("invalid_payload")
    return {
        "nombre": payload.get("nombre") or "",
        "whatsapp": payload.get("whatsapp") or payload.get("telefono") or "",
        "email": payload.get("email") or "",
        "rubro": payload.get("rubro") or "",
        "pais": payload.get("pais") or "",
    }
