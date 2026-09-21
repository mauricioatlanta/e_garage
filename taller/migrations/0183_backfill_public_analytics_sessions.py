import copy
import hashlib
import json
import logging
import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone as dt_timezone

from django.db import migrations, transaction
from django.db.models import Exists, OuterRef, Q
from django.db.models.functions import Trim
from django.utils import timezone


logger = logging.getLogger(__name__)

LEGACY_EVENT_TYPES = {
    "landing_view",
    "cta_click",
    "signup_start",
    "signup_complete",
    "onboarding_complete",
    "subscription_paid",
}

MAPPING_VERSION = 1
ATTRIBUTION_DAYS = 30
SESSION_NAMESPACE = "legacy-public-analytics-session:v1:"
VISITOR_NAMESPACE = "legacy-public-analytics-visitor:v1:"
MAX_CONFLICT_DETAILS = 20
BATCH_SIZE = 500
CHECKPOINT_KEY = "public_analytics_legacy_v1"
CHECKPOINT_READY = "READY"
CHECKPOINT_RUNNING = "RUNNING"
CHECKPOINT_COMPLETED = "COMPLETED"
CHECKPOINT_FAILED = "FAILED"
# Long enough for one identity transaction, short enough for crash recovery.
LEASE_DURATION = timedelta(minutes=15)
# A group can contain many rows, so ownership is refreshed by elapsed time as
# well as at group boundaries.  Keeping this well below the lease duration
# leaves room for a slow database operation and crash recovery.
LEASE_HEARTBEAT_INTERVAL = timedelta(seconds=30)

TRIAL_CTA_IDS = {
    "trial_30",
    "trial_30_days",
    "cta_trial_30",
    "cta_trial_30_click",
}

TRIAL_CTA_TYPES = {"trial_30", "trial_30_days"}
METADATA_KINDS = {"object", "json_null", "list", "string", "number", "boolean"}


class LeaseBusy(Exception):
    """The checkpoint is owned by another live execution."""


class LeaseLost(Exception):
    """This execution no longer owns the checkpoint."""


def _clock():
    return timezone.now()


class LeaseHeartbeat:
    def __init__(self, Checkpoint, token, clock=None, interval=None):
        self.Checkpoint = Checkpoint
        self.token = token
        self.clock = clock or _clock
        self.interval = interval or LEASE_HEARTBEAT_INTERVAL
        self.last_renewed_at = self.clock()

    def __call__(self):
        now = self.clock()
        if now - self.last_renewed_at < self.interval:
            return
        _renew_lease(self.Checkpoint, self.token, now=now)
        self.last_renewed_at = now

    def force(self):
        now = self.clock()
        _renew_lease(self.Checkpoint, self.token, now=now)
        self.last_renewed_at = now


def _lease_boundary(lease_guard):
    if lease_guard is None:
        return
    force = getattr(lease_guard, "force", None)
    (force or lease_guard)()


def _blank(value):
    return value is None or (isinstance(value, str) and not value.strip())


def _clean(value, limit):
    if value is None:
        return ""
    return str(value).strip()[:limit]


def _identity_hash(namespace, identity):
    return hashlib.sha256(f"{namespace}{identity}".encode("utf-8")).hexdigest()


def _session_hash(identity):
    return _identity_hash(SESSION_NAMESPACE, identity)


def _visitor_hash(identity):
    return _identity_hash(VISITOR_NAMESPACE, identity)


def _valid_visitor_hash(value):
    if not isinstance(value, str):
        return False
    value = value.strip()
    return len(value) == 64 and all(character in "0123456789abcdefABCDEF" for character in value)


def _identity_for_key(session_key):
    return f"key:{session_key.strip()}"


def _identity_for_page(page_view):
    return f"page:{page_view.pk}"


def _identity_for_event(event):
    return f"event:{event.pk}"


def _is_legacy_event(event):
    return event.event_type in LEGACY_EVENT_TYPES


def _mapping_is_allowed(legacy_type, mapped_type):
    allowed = {
        "landing_view": {"landing_view", "human_visit"},
        "signup_start": {"signup_start", "signup_started"},
        "signup_complete": {"signup_complete", "signup_completed"},
        "cta_click": {"cta_click", "cta_trial_30_click"},
        "onboarding_complete": {"onboarding_complete"},
        "subscription_paid": {"subscription_paid"},
    }
    return legacy_type in allowed and mapped_type in allowed[legacy_type]


def _event_scope(Event, cutoff_pk):
    if cutoff_pk is None:
        return Event.objects.none()
    return Event.objects.filter(pk__lte=cutoff_pk)


def _page_scope(PageView, cutoff_pk):
    if cutoff_pk is None:
        return PageView.objects.none()
    return PageView.objects.filter(pk__lte=cutoff_pk)


def _legacy_pageviews(Event, PageView, event_cutoff_pk, pageview_cutoff_pk):
    scoped_events = _event_scope(Event, event_cutoff_pk)
    scoped_pages = _page_scope(PageView, pageview_cutoff_pk)
    any_event = scoped_events.filter(page_view_id=OuterRef("pk"))
    legacy_event = scoped_events.filter(
        page_view_id=OuterRef("pk"),
        event_type__in=LEGACY_EVENT_TYPES,
    )
    return scoped_pages.annotate(
        _has_any_event=Exists(any_event),
        _has_legacy_event=Exists(legacy_event),
    ).filter(
        Q(_has_any_event=False) | Q(_has_legacy_event=True),
    )


def _has_valid_ledger(event):
    metadata = event.metadata
    if not isinstance(metadata, dict):
        return False
    ledger = metadata.get("_legacy_reconstruction")
    if not (
        isinstance(ledger, dict)
        and ledger.get("version") == MAPPING_VERSION
        and ledger.get("legacy_event_id") == event.pk
        and _ledger_digest_is_valid(ledger)
    ):
        return False

    required = {
        "version", "legacy_event_id", "legacy_event_type", "mapped_event_type",
        "fields_filled", "fields_changed", "original_metadata_kind",
        "original_metadata_wrapped", "ledger_digest",
    }
    if not required.issubset(ledger) or set(ledger) - required - {"original_metadata_digest"}:
        return False
    if not isinstance(ledger["fields_filled"], list) or not isinstance(ledger["fields_changed"], list):
        return False
    if any(field not in {"session_id", "dedupe_key", "occurred_at"} for field in ledger["fields_filled"]):
        return False
    if any(field not in {"metadata", "event_type"} for field in ledger["fields_changed"]):
        return False
    if len(ledger["fields_filled"]) != len(set(ledger["fields_filled"])):
        return False
    if len(ledger["fields_changed"]) != len(set(ledger["fields_changed"])):
        return False
    if ledger["legacy_event_type"] not in LEGACY_EVENT_TYPES:
        return False
    if not _mapping_is_allowed(ledger["legacy_event_type"], ledger["mapped_event_type"]):
        return False
    if (ledger["mapped_event_type"] != ledger["legacy_event_type"]) != (
        "event_type" in ledger["fields_changed"]
    ):
        return False
    if "metadata" not in ledger["fields_changed"]:
        return False
    if ledger["original_metadata_kind"] not in METADATA_KINDS:
        return False
    if ledger["original_metadata_wrapped"] != (ledger["original_metadata_kind"] != "object"):
        return False
    if ledger["mapped_event_type"] != event.event_type:
        return False
    if ledger["original_metadata_kind"] == "object":
        if "original_metadata_digest" not in ledger or ledger["original_metadata_wrapped"]:
            return False
        if "_legacy_original_metadata" in metadata:
            return False
        protected_metadata = dict(metadata)
        protected_metadata.pop("_legacy_reconstruction", None)
        if ledger["original_metadata_digest"] != _json_digest(protected_metadata):
            return False
    else:
        original = metadata.get("_legacy_original_metadata")
        if not ledger["original_metadata_wrapped"] or not isinstance(original, dict):
            return False
        if original.get("kind") != ledger["original_metadata_kind"] or "value" not in original:
            return False
    return True


def _has_ledger_conflict(event):
    if not isinstance(event.metadata, dict):
        return False
    ledger = event.metadata.get("_legacy_reconstruction")
    if ledger is None:
        return False
    return not _has_valid_ledger(event)


def _sort_key(source):
    kind, row = source
    timestamp = row.created_at
    if timestamp is None:
        timestamp = datetime.min.replace(tzinfo=dt_timezone.utc)
    return (timestamp, 0 if kind == "page_view" else 1, row.pk)


def _sources(event_rows, page_view_rows):
    return sorted(
        [("page_view", row) for row in page_view_rows]
        + [("event", row) for row in event_rows],
        key=_sort_key,
    )


def _source_value(kind, row, field):
    return getattr(row, field, "") if hasattr(row, field) else ""


def _first_non_blank(sources, field, limit):
    for kind, row in sources:
        value = _source_value(kind, row, field)
        if not _blank(value):
            return _clean(value, limit)
    return ""


def _last_non_blank(sources, field, limit):
    for kind, row in reversed(sources):
        value = _source_value(kind, row, field)
        if not _blank(value):
            return _clean(value, limit)
    return ""


def _vertical_from_path(path):
    path = (path or "").lower()
    if "/desarmadurias/" in path:
        return "salvage"
    return ""


def _profile(event_rows, page_view_rows, identity):
    sources = _sources(event_rows, page_view_rows)
    timed_sources = [source for source in sources if source[1].created_at is not None]
    if not timed_sources:
        return None

    first_source = timed_sources[0]
    last_source = timed_sources[-1]
    first_seen_at = first_source[1].created_at
    last_seen_at = last_source[1].created_at

    first_path = _first_non_blank(sources, "path", 255)
    last_path = _last_non_blank(sources, "path", 255)
    landing_path = _first_non_blank(sources, "landing_initial", 255) or first_path

    page_type = _first_non_blank(sources, "page_type", 20)
    vertical_key = _first_non_blank(sources, "rubro", 40)
    if not vertical_key:
        for candidate in (first_path, landing_path):
            vertical_key = _vertical_from_path(candidate)
            if vertical_key:
                break

    utm_source = ""
    utm_medium = ""
    utm_campaign = ""
    utm_term = ""
    utm_content = ""
    for kind, row in sources:
        candidate = {
            "utm_source": _clean(_source_value(kind, row, "utm_source"), 100),
            "utm_medium": _clean(_source_value(kind, row, "utm_medium"), 100),
            "utm_campaign": _clean(_source_value(kind, row, "utm_campaign"), 150),
            "utm_term": _clean(_source_value(kind, row, "utm_term"), 150),
            "utm_content": _clean(_source_value(kind, row, "utm_content"), 150),
        }
        if any(candidate.values()):
            utm_source = candidate["utm_source"]
            utm_medium = candidate["utm_medium"]
            utm_campaign = candidate["utm_campaign"]
            utm_term = candidate["utm_term"]
            utm_content = candidate["utm_content"]
            break

    initial_referrer = _first_non_blank(sources, "referrer", 500)
    last_referrer = _last_non_blank(sources, "referrer", 500)
    country = _first_non_blank(sources, "country", 8).lower()
    language = _first_non_blank(sources, "language", 8).lower()
    user_agent = _first_non_blank(sources, "user_agent", 500)
    visitor_hash = ""
    for kind, row in sources:
        candidate = _source_value(kind, row, "visitor_hash")
        if _valid_visitor_hash(candidate):
            visitor_hash = candidate.strip().lower()
            break
    visitor_hash = visitor_hash or _visitor_hash(identity)

    is_mobile = any(bool(getattr(row, "is_mobile", False)) for _, row in sources)
    is_bot = any(bool(getattr(row, "is_bot", False)) for _, row in sources)
    is_internal = any(
        bool(
            getattr(row, "is_internal", False)
            or getattr(row, "is_staff", False)
            or getattr(row, "is_server", False)
        )
        for _, row in sources
    )

    if any((utm_source, utm_medium, utm_campaign)):
        attribution_type = "utm"
    elif initial_referrer:
        attribution_type = "referrer"
    else:
        attribution_type = "direct"

    return {
        "anonymous_visitor_hash": visitor_hash,
        "first_path": first_path,
        "last_path": last_path,
        "landing_path": landing_path,
        "country": country,
        "language": language,
        "vertical_key": _clean(vertical_key, 40),
        "page_type": page_type,
        "initial_referrer": initial_referrer,
        "last_referrer": last_referrer,
        "utm_source": utm_source,
        "utm_medium": utm_medium,
        "utm_campaign": utm_campaign,
        "utm_term": utm_term,
        "utm_content": utm_content,
        "gclid": "",
        "fbclid": "",
        "msclkid": "",
        "attribution_type": attribution_type,
        "user_agent": user_agent,
        "is_mobile": is_mobile,
        "is_bot": is_bot,
        "is_internal": is_internal,
        "ip_hash": "",
        "first_seen_at": first_seen_at,
        "last_seen_at": last_seen_at,
        "expires_at": first_seen_at + timedelta(days=ATTRIBUTION_DAYS),
    }


def _metadata_kind(value):
    if value is None:
        return "json_null"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "list"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    raise ValueError("unsupported_metadata_type")


def _json_digest(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _trial_cta_is_explicit(metadata):
    if not isinstance(metadata, dict):
        return False
    cta_id = str(metadata.get("cta_id") or "").strip().lower()
    cta_type = str(metadata.get("cta_type") or "").strip().lower()
    return cta_id in TRIAL_CTA_IDS or cta_type in TRIAL_CTA_TYPES


def _map_event(event, is_bot, is_internal):
    if event.event_type == "landing_view" and not is_bot and not is_internal:
        return "human_visit"
    if event.event_type == "signup_start" and not is_bot and not is_internal:
        return "signup_started"
    if event.event_type == "signup_complete" and not is_bot and not is_internal:
        return "signup_completed"
    if event.event_type == "cta_click" and _trial_cta_is_explicit(event.metadata):
        return "cta_trial_30_click"
    return event.event_type


def _prepare_metadata(event, mapped_event_type):
    metadata = event.metadata
    if isinstance(metadata, dict):
        if "_legacy_reconstruction" in metadata or "_legacy_original_metadata" in metadata:
            raise ValueError("reserved_metadata_key")
        original_kind = "object"
        original_digest = _json_digest(metadata)
        result = copy.deepcopy(metadata)
        wrapped = False
    else:
        original_kind = _metadata_kind(metadata)
        original_digest = ""
        result = {
            "_legacy_original_metadata": {
                "kind": original_kind,
                "value": copy.deepcopy(metadata),
            }
        }
        wrapped = True

    fields_changed = ["metadata"]
    if mapped_event_type != event.event_type:
        fields_changed.append("event_type")

    ledger = {
        "version": MAPPING_VERSION,
        "legacy_event_id": event.pk,
        "legacy_event_type": event.event_type,
        "mapped_event_type": mapped_event_type,
        "fields_filled": [],
        "fields_changed": fields_changed,
        "original_metadata_kind": original_kind,
        "original_metadata_wrapped": wrapped,
    }
    if original_digest:
        ledger["original_metadata_digest"] = original_digest
    result["_legacy_reconstruction"] = ledger
    return result, ledger


def _identity_for_event_with_page(event, page_view):
    if not _blank(event.session_key):
        return _identity_for_key(event.session_key)
    if page_view is not None:
        if not _blank(page_view.session_key):
            return _identity_for_key(page_view.session_key)
        return _identity_for_page(page_view)
    return _identity_for_event(event)


def _identity_for_page_key(page_view):
    if not _blank(page_view.session_key):
        return _identity_for_key(page_view.session_key)
    return _identity_for_page(page_view)


def _distinct_sessions(event_rows, page_views):
    ids = set(
        row.public_session_id
        for row in page_views
        if row.public_session_id is not None
    )
    ids.update(row.session_id for row in event_rows if row.session_id is not None)
    return ids


def _log_conflict(counters, identity, reason, session_ids=None):
    counters["events_conflicted"] += 1 if reason != "page_view" else 0
    counters["identity_conflicts"] += reason == "multiple_sessions_for_identity"
    if counters["conflict_details"] < MAX_CONFLICT_DETAILS:
        logger.warning(
            "public analytics 0183 conflict identity_hash=%s reason=%s session_ids=%s",
            hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16],
            reason,
            sorted(session_ids or []),
        )
        counters["conflict_details"] += 1


def _get_or_create_session(Session, identity, profile, counters):
    expected_hash = _session_hash(identity)
    session = Session.objects.filter(anonymous_session_hash=expected_hash).first()
    if session is not None:
        counters["sessions_reused"] += 1
        return session

    session = Session.objects.create(
        anonymous_session_hash=expected_hash,
        **profile,
    )
    counters["sessions_created"] += 1
    return session


def _event_is_internal(event, page_views):
    return bool(
        getattr(event, "is_internal", False)
        or getattr(event, "is_staff", False)
        or getattr(event, "is_server", False)
        or any(
            getattr(page, "is_internal", False)
            or getattr(page, "is_staff", False)
            or getattr(page, "is_server", False)
            for page in page_views
        )
    )


def _event_is_bot(event, page_views):
    return bool(
        getattr(event, "is_bot", False)
        or any(getattr(page, "is_bot", False) for page in page_views)
    )


def _process_group(
    Event,
    PageView,
    Session,
    identity,
    event_rows,
    page_view_rows,
    counters,
    lease_guard=None,
):
    pending_events = [
        event for event in event_rows
        if _is_legacy_event(event) and not _has_valid_ledger(event)
    ]
    pending_page_views = [
        page for page in page_view_rows
        if page.public_session_id is None
    ]
    if not pending_events and not pending_page_views:
        counters["events_skipped"] += len(event_rows)
        counters["pageviews_skipped"] += len(page_view_rows)
        return False

    session_ids = _distinct_sessions(event_rows, page_view_rows)
    if len(session_ids) > 1:
        _log_conflict(counters, identity, "multiple_sessions_for_identity", session_ids)
        counters["pageviews_conflicted"] += len(pending_page_views)
        return False

    non_blank_keys = {
        row.session_key.strip()
        for row in list(event_rows) + list(page_view_rows)
        if not _blank(row.session_key)
    }
    if len(non_blank_keys) > 1:
        _log_conflict(counters, identity, "incompatible_session_keys", non_blank_keys)
        counters["pageviews_conflicted"] += len(pending_page_views)
        counters["events_conflicted"] += len(pending_events)
        return False
    if identity.startswith("key:") and non_blank_keys != {identity[4:]}:
        _log_conflict(counters, identity, "incompatible_session_key", non_blank_keys)
        counters["pageviews_conflicted"] += len(pending_page_views)
        counters["events_conflicted"] += len(pending_events)
        return False

    valid_events = []
    for event in pending_events:
        if _has_ledger_conflict(event):
            _log_conflict(counters, identity, "ledger_conflict")
            continue
        if event.created_at is None:
            counters["missing_timestamp_rows"] += 1
            _log_conflict(counters, identity, "missing_created_at")
            continue
        try:
            mapped_type = _map_event(
                event,
                _event_is_bot(event, page_view_rows),
                _event_is_internal(event, page_view_rows),
            )
            metadata, ledger = _prepare_metadata(event, mapped_type)
        except (TypeError, ValueError, OverflowError) as exc:
            counters["metadata_conflicts"] += 1
            _log_conflict(counters, identity, str(exc))
            continue
        valid_events.append((event, mapped_type, metadata, ledger))

    if not valid_events and not pending_page_views:
        return False

    profile = _profile(event_rows, page_view_rows, identity)
    if profile is None:
        counters["missing_timestamp_rows"] += len(valid_events)
        _log_conflict(counters, identity, "missing_group_timestamp")
        return False

    # The validation above is deliberately outside the write transactions.  A
    # group may be large, so each row gets its own short transaction and the
    # heartbeat can fence ownership between rows.
    session = None
    if session_ids:
        session_id = next(iter(session_ids))
    else:
        session_id = None

    def ensure_session():
        nonlocal session, session_id
        if session is not None:
            return session
        if session_id is not None:
            session = Session.objects.get(pk=session_id)
            counters["sessions_reused"] += 1
        else:
            session = _get_or_create_session(Session, identity, profile, counters)
            session_id = session.pk
        return session

    for page_view in pending_page_views:
        if lease_guard:
            lease_guard()
        with transaction.atomic():
            current_page = PageView.objects.select_for_update().get(pk=page_view.pk)
            if current_page.public_session_id is not None:
                continue
            current_session = ensure_session()
            current_page.public_session_id = current_session.pk
            current_page.save(update_fields=["public_session"])
            counters["pageviews_linked"] += 1
        if lease_guard:
            lease_guard()

    for event, mapped_type, metadata, ledger in valid_events:
        if lease_guard:
            lease_guard()
        with transaction.atomic():
            current_event = Event.objects.select_for_update().get(pk=event.pk)
            if _has_valid_ledger(current_event):
                counters["events_skipped"] += 1
                continue
            current_session = ensure_session()
            if current_event.session_id is not None and current_event.session_id != current_session.pk:
                _log_conflict(counters, identity, "session_changed_during_group")
                continue
            event_ledger = copy.deepcopy(ledger)
            if current_event.session_id is None:
                current_event.session_id = current_session.pk
                event_ledger["fields_filled"].append("session_id")
            if _blank(current_event.dedupe_key):
                current_event.dedupe_key = f"legacy-event-{current_event.pk}"
                event_ledger["fields_filled"].append("dedupe_key")
            if current_event.occurred_at is None:
                current_event.occurred_at = current_event.created_at
                event_ledger["fields_filled"].append("occurred_at")
            if mapped_type != current_event.event_type:
                current_event.event_type = mapped_type
                counters["events_mapped"] += 1
            else:
                counters["events_legacy_preserved"] += 1
            event_ledger["ledger_digest"] = _json_digest(
                {key: value for key, value in event_ledger.items() if key != "ledger_digest"}
            )
            event_metadata = copy.deepcopy(metadata)
            event_metadata["_legacy_reconstruction"] = event_ledger
            current_event.metadata = event_metadata
            current_event.save()
            counters["events_processed"] += 1
        if lease_guard:
            lease_guard()

    return bool(valid_events or pending_page_views)


def _process_key_groups(
    Event,
    PageView,
    Session,
    counters,
    event_cutoff_pk,
    pageview_cutoff_pk,
    lease_guard=None,
):
    progress = False
    scoped_events = _event_scope(Event, event_cutoff_pk)
    event_keys = scoped_events.filter(event_type__in=LEGACY_EVENT_TYPES).exclude(
        session_key__isnull=True,
    ).annotate(
        _normalized_key=Trim("session_key"),
    ).filter(
        _normalized_key__gt="",
    ).order_by().values_list("_normalized_key", flat=True)
    page_keys = _legacy_pageviews(
        Event, PageView, event_cutoff_pk, pageview_cutoff_pk,
    ).exclude(session_key__isnull=True).annotate(
        _normalized_key=Trim("session_key"),
    ).filter(
        _normalized_key__gt="",
    ).order_by().values_list("_normalized_key", flat=True)
    key_source = event_keys.union(page_keys).iterator(
        chunk_size=BATCH_SIZE,
    )
    for normalized_key in key_source:
        _lease_boundary(lease_guard)
        page_views = list(
            _legacy_pageviews(
                Event, PageView, event_cutoff_pk, pageview_cutoff_pk,
            ).annotate(_normalized_key=Trim("session_key"))
            .filter(_normalized_key=normalized_key)
            .order_by("created_at", "pk")
        )
        related_page_ids = list(
            scoped_events.filter(
                event_type__in=LEGACY_EVENT_TYPES,
                page_view_id__isnull=False,
            ).annotate(_normalized_key=Trim("session_key"))
            .filter(_normalized_key=normalized_key)
            .values_list("page_view_id", flat=True)
        )
        if related_page_ids:
            page_views.extend(
                _legacy_pageviews(
                    Event, PageView, event_cutoff_pk, pageview_cutoff_pk,
                ).filter(
                    pk__in=related_page_ids,
                )
                .order_by("created_at", "pk")
            )
        page_views = {page.pk: page for page in page_views}
        page_views = list(sorted(page_views.values(), key=lambda page: (page.created_at, page.pk)))
        page_ids = [page.pk for page in page_views]
        events = list(
            scoped_events.filter(
                event_type__in=LEGACY_EVENT_TYPES,
            ).annotate(_normalized_key=Trim("session_key"))
            .filter(_normalized_key=normalized_key)
            .order_by("created_at", "pk")
        )
        if page_ids:
            events.extend(
                scoped_events.filter(
                    event_type__in=LEGACY_EVENT_TYPES,
                    page_view_id__in=page_ids,
                ).order_by("created_at", "pk")
            )
        deduped_events = {event.pk: event for event in events}
        related_keys = {
            row.session_key.strip()
            for row in page_views
            if not _blank(row.session_key)
        }
        related_keys.update(
            row.session_key.strip()
            for row in deduped_events.values()
            if not _blank(row.session_key)
        )
        if len(related_keys) > 1:
            identity = _identity_for_key(normalized_key)
            _log_conflict(counters, identity, "incompatible_related_session_keys", related_keys)
            counters["events_conflicted"] += sum(
                1 for row in deduped_events.values() if _is_legacy_event(row)
            )
            counters["pageviews_conflicted"] += sum(
                1 for row in page_views if row.public_session_id is None
            )
            continue
        identity = _identity_for_key(normalized_key)
        progress = _process_group(
            Event,
            PageView,
            Session,
            identity,
            list(deduped_events.values()),
            page_views,
            counters,
            lease_guard=lease_guard,
        ) or progress
        _lease_boundary(lease_guard)
    return progress


def _process_page_groups(
    Event,
    PageView,
    Session,
    counters,
    event_cutoff_pk,
    pageview_cutoff_pk,
    lease_guard=None,
):
    progress = False
    scoped_events = _event_scope(Event, event_cutoff_pk)
    scoped_pages = _page_scope(PageView, pageview_cutoff_pk)
    page_id_iterator = scoped_events.filter(
        event_type__in=LEGACY_EVENT_TYPES,
        page_view_id__isnull=False,
    ).annotate(_normalized_key=Trim("session_key")).filter(
        _normalized_key="",
    ).values_list("page_view_id", flat=True).distinct().iterator(chunk_size=BATCH_SIZE)
    for page_id in page_id_iterator:
        _lease_boundary(lease_guard)
        page_view = scoped_pages.filter(pk=page_id).first()
        if page_view is None or not _blank(page_view.session_key):
            continue
        events = list(
            scoped_events.filter(page_view_id=page_id).order_by("created_at", "pk")
        )
        progress = _process_group(
            Event,
            PageView,
            Session,
            _identity_for_page(page_view),
            events,
            [page_view],
            counters,
            lease_guard=lease_guard,
        ) or progress
        _lease_boundary(lease_guard)
    return progress


def _process_orphan_events(Event, PageView, Session, counters, event_cutoff_pk, lease_guard=None):
    progress = False
    events = _event_scope(Event, event_cutoff_pk).filter(
        event_type__in=LEGACY_EVENT_TYPES,
        page_view_id__isnull=True,
    ).order_by("pk").iterator(chunk_size=BATCH_SIZE)
    for event in events:
        _lease_boundary(lease_guard)
        if not _blank(event.session_key):
            continue
        progress = _process_group(
            Event,
            PageView,
            Session,
            _identity_for_event(event),
            [event],
            [],
            counters,
            lease_guard=lease_guard,
        ) or progress
        _lease_boundary(lease_guard)
    return progress


def _new_counters():
    return Counter(
        events_seen=0,
        events_processed=0,
        events_skipped=0,
        events_conflicted=0,
        events_mapped=0,
        events_legacy_preserved=0,
        pageviews_seen=0,
        pageviews_linked=0,
        pageviews_skipped=0,
        pageviews_conflicted=0,
        sessions_created=0,
        sessions_reused=0,
        identity_conflicts=0,
        metadata_conflicts=0,
        missing_timestamp_rows=0,
        conflict_details=0,
    )


def _acquire_lease(Checkpoint, now=None, token=None):
    now = now or timezone.now()
    token = token or uuid.uuid4().hex
    expires_at = now + LEASE_DURATION
    with transaction.atomic():
        checkpoint = Checkpoint.objects.filter(key=CHECKPOINT_KEY).first()
        if checkpoint is None:
            raise RuntimeError("0183 checkpoint public_analytics_legacy_v1 is missing")
        if checkpoint.status == CHECKPOINT_COMPLETED:
            return None, token
        if checkpoint.status not in {
            CHECKPOINT_READY,
            CHECKPOINT_RUNNING,
            CHECKPOINT_FAILED,
        }:
            raise RuntimeError(f"0183 checkpoint has unsupported status: {checkpoint.status}")

        available = Q(status__in=[CHECKPOINT_READY, CHECKPOINT_FAILED]) | Q(
            status=CHECKPOINT_RUNNING,
        ) & Q(
            Q(lease_expires_at__isnull=True) | Q(lease_expires_at__lte=now),
        )
        updated = Checkpoint.objects.filter(
            key=CHECKPOINT_KEY,
        ).filter(available).update(
            status=CHECKPOINT_RUNNING,
            owner_token=token,
            lease_expires_at=expires_at,
            completed_at=None,
        )
        if not updated:
            raise LeaseBusy("0183 checkpoint is already owned by a live execution")
        checkpoint = Checkpoint.objects.get(key=CHECKPOINT_KEY)
    return checkpoint, token


def _renew_lease(Checkpoint, token, now=None):
    now = now or _clock()
    updated = Checkpoint.objects.filter(
        key=CHECKPOINT_KEY,
        status=CHECKPOINT_RUNNING,
        owner_token=token,
    ).update(lease_expires_at=now + LEASE_DURATION)
    if not updated:
        raise LeaseLost("0183 lease was lost")


def _owned_update(Checkpoint, token, **values):
    updated = Checkpoint.objects.filter(
        key=CHECKPOINT_KEY,
        status=CHECKPOINT_RUNNING,
        owner_token=token,
    ).update(**values)
    if not updated:
        raise LeaseLost("0183 lease was lost")


def forwards(apps, schema_editor):
    Event = apps.get_model("taller", "PublicAnalyticsEvent")
    PageView = apps.get_model("taller", "PublicPageView")
    Session = apps.get_model("taller", "PublicAnalyticsSession")
    Checkpoint = apps.get_model("taller", "PublicAnalyticsBackfillCheckpoint")
    checkpoint, owner_token = _acquire_lease(Checkpoint)
    if checkpoint is None:
        logger.info("public analytics 0183 already completed; no-op")
        return

    event_cutoff_pk = checkpoint.cutoff_event_pk
    pageview_cutoff_pk = checkpoint.cutoff_pageview_pk
    counters = _new_counters()

    heartbeat = LeaseHeartbeat(Checkpoint, owner_token)
    try:
        heartbeat.force()
        counters["events_seen"] = _event_scope(Event, event_cutoff_pk).filter(
            event_type__in=LEGACY_EVENT_TYPES,
        ).count()
        eligible_pageviews = _legacy_pageviews(
            Event, PageView, event_cutoff_pk, pageview_cutoff_pk,
        ).annotate(
            _normalized_key=Trim("session_key"),
        ).filter(Q(_normalized_key__gt="") | Q(_has_legacy_event=True))
        counters["pageviews_seen"] = eligible_pageviews.count()
        _process_key_groups(
            Event,
            PageView,
            Session,
            counters,
            event_cutoff_pk,
            pageview_cutoff_pk,
            heartbeat,
        )
        _process_page_groups(
            Event,
            PageView,
            Session,
            counters,
            event_cutoff_pk,
            pageview_cutoff_pk,
            heartbeat,
        )
        _process_orphan_events(
            Event,
            PageView,
            Session,
            counters,
            event_cutoff_pk,
            heartbeat,
        )
    except Exception:
        try:
            Checkpoint.objects.filter(
                key=CHECKPOINT_KEY,
                status=CHECKPOINT_RUNNING,
                owner_token=owner_token,
            ).update(
                status=CHECKPOINT_FAILED,
                summary={key: value for key, value in counters.items() if key != "conflict_details"},
                owner_token=None,
                lease_expires_at=None,
            )
        except Exception:
            logger.exception("public analytics 0183 could not persist FAILED state")
        raise

    summary = {key: value for key, value in counters.items() if key != "conflict_details"}
    _owned_update(
        Checkpoint,
        owner_token,
        status=CHECKPOINT_COMPLETED,
        completed_at=timezone.now(),
        summary=summary,
        owner_token=None,
        lease_expires_at=None,
    )
    logger.info(
        "public analytics 0183 summary cutoff_event_pk=%s cutoff_pageview_pk=%s %s",
        event_cutoff_pk,
        pageview_cutoff_pk,
        summary,
    )


def _expected_identity_for_reverse(event, PageView, pageview_cutoff_pk):
    page_view = (
        _page_scope(PageView, pageview_cutoff_pk).filter(pk=event.page_view_id).first()
        if event.page_view_id else None
    )
    return _identity_for_event_with_page(event, page_view)


def _restore_metadata(event, ledger):
    metadata = event.metadata
    if not isinstance(metadata, dict):
        return metadata, False
    kind = ledger.get("original_metadata_kind")
    if ledger.get("original_metadata_wrapped"):
        expected = {
            "_legacy_original_metadata": metadata.get("_legacy_original_metadata"),
            "_legacy_reconstruction": metadata.get("_legacy_reconstruction"),
        }
        if metadata != expected:
            return metadata, False
        original = metadata.get("_legacy_original_metadata") or {}
        if original.get("kind") != kind:
            return metadata, False
        return copy.deepcopy(original.get("value")), True

    restored = copy.deepcopy(metadata)
    restored.pop("_legacy_reconstruction", None)
    if ledger.get("original_metadata_digest") != _json_digest(restored):
        return metadata, False
    return restored, True


def _ledger_digest_is_valid(ledger):
    digest = ledger.get("ledger_digest")
    if not digest:
        return False
    expected = _json_digest(
        {key: value for key, value in ledger.items() if key != "ledger_digest"}
    )
    return digest == expected


def backwards(apps, schema_editor):
    Event = apps.get_model("taller", "PublicAnalyticsEvent")
    PageView = apps.get_model("taller", "PublicPageView")
    Session = apps.get_model("taller", "PublicAnalyticsSession")
    Checkpoint = apps.get_model("taller", "PublicAnalyticsBackfillCheckpoint")
    checkpoint = Checkpoint.objects.filter(key=CHECKPOINT_KEY).first()
    if checkpoint is None:
        logger.warning("public analytics 0183 reverse skipped: checkpoint is missing")
        return
    # Fence any forward executor before restoring rows.
    Checkpoint.objects.filter(key=CHECKPOINT_KEY).update(
        status=CHECKPOINT_READY,
        owner_token=None,
        lease_expires_at=None,
        completed_at=None,
    )
    event_cutoff_pk = checkpoint.cutoff_event_pk
    pageview_cutoff_pk = checkpoint.cutoff_pageview_pk

    for event in _event_scope(Event, event_cutoff_pk).iterator(chunk_size=500):
        metadata = event.metadata
        ledger = metadata.get("_legacy_reconstruction") if isinstance(metadata, dict) else None
        if not _has_valid_ledger(event):
            continue

        changed = False
        if "event_type" in ledger.get("fields_changed", []):
            if event.event_type == ledger.get("mapped_event_type"):
                event.event_type = ledger.get("legacy_event_type")
                changed = True

        if "session_id" in ledger.get("fields_filled", []):
            identity = _expected_identity_for_reverse(event, PageView, pageview_cutoff_pk)
            expected_hash = _session_hash(identity)
            session = Session.objects.filter(pk=event.session_id).first()
            if session is not None and session.anonymous_session_hash == expected_hash:
                event.session_id = None
                changed = True

        if "dedupe_key" in ledger.get("fields_filled", []):
            expected_key = f"legacy-event-{event.pk}"
            if event.dedupe_key == expected_key:
                event.dedupe_key = None
                changed = True

        if "occurred_at" in ledger.get("fields_filled", []):
            if event.occurred_at == event.created_at:
                event.occurred_at = None
                changed = True

        restored_metadata, metadata_restored = _restore_metadata(event, ledger)
        if metadata_restored:
            event.metadata = restored_metadata
            changed = True

        if changed:
            event.save()

    Checkpoint.objects.filter(key=CHECKPOINT_KEY).update(
        status=CHECKPOINT_READY,
        owner_token=None,
        lease_expires_at=None,
        completed_at=None,
    )
    logger.warning(
        "public analytics 0183 reverse is conservative: synthetic sessions are retained "
        "and PublicPageView.public_session is not cleared; restore backup for exact rollback"
    )


class Migration(migrations.Migration):
    atomic = False

    dependencies = [("taller", "0182_public_analytics_backfill_checkpoint")]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
