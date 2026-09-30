from django.http import JsonResponse
from django.views.decorators.http import require_POST

from taller.services.public_event_tracking import (
    PublicEventValidationError,
    check_public_event_rate_limit,
    get_session_from_request_cookie,
    parse_public_event_payload,
    record_public_event,
    validate_public_event_payload,
)


@require_POST
def public_analytics_event(request):
    session = get_session_from_request_cookie(request)
    if session is None:
        return JsonResponse({"ok": False, "error": "session_required"}, status=400)

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
        return response

    try:
        payload = parse_public_event_payload(request)
        event_type, path, dedupe_key, metadata = validate_public_event_payload(payload)
    except PublicEventValidationError as exc:
        return JsonResponse({"ok": False, "error": exc.code}, status=exc.status)

    if session.is_bot or session.is_internal:
        return JsonResponse({"ok": True, "created": False, "ignored": True})

    event, created = record_public_event(
        session=session,
        event_type=event_type,
        path=path,
        dedupe_key=dedupe_key,
        metadata=metadata,
    )
    return JsonResponse({"ok": True, "created": created, "event_id": event.pk})
