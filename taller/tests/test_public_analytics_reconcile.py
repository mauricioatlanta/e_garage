from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase, override_settings
from django.contrib.sessions.backends.db import SessionStore
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from datetime import timedelta
import importlib

from taller.models.public_page_view import PublicAnalyticsEvent
from taller.models.public_page_view import PublicPageView
from taller.models.public_analytics_backfill_checkpoint import PublicAnalyticsBackfillCheckpoint
from taller.models.public_analytics_session import PublicAnalyticsSession
from taller.models.registro_embudo import RegistroEmbudoSuscriptor
from taller.services.registro_embudo_service import registrar_primer_login


class PublicAnalyticsReconcileTests(TestCase):
    def _request(self, user):
        request = RequestFactory().get("/cl/es/landing/")
        request.session = SessionStore()
        request.user = user
        return request

    def test_first_login_is_canonical_and_idempotent(self):
        user = get_user_model().objects.create_user(
            username="analytics-reconcile@example.test",
            email="analytics-reconcile@example.test",
            password="password",
        )
        RegistroEmbudoSuscriptor.objects.create(
            user=user,
            pais="CL",
            fecha_registro=timezone.now(),
        )
        request = self._request(user)

        registrar_primer_login(user, request=request)
        registrar_primer_login(user, request=request)

        self.assertEqual(
            PublicAnalyticsEvent.objects.filter(
                event_type=PublicAnalyticsEvent.EVENT_FIRST_LOGIN
            ).count(),
            1,
        )
        self.assertIsNotNone(
            RegistroEmbudoSuscriptor.objects.get(user=user).primer_login_at
        )

    @override_settings(PUBLIC_ANALYTICS_QA_EMAIL_DOMAIN="example.test")
    def test_qa_domain_does_not_emit_first_login(self):
        user = get_user_model().objects.create_user(
            username="qa@example.test",
            email="qa@example.test",
            password="password",
        )
        RegistroEmbudoSuscriptor.objects.create(
            user=user,
            pais="CL",
            fecha_registro=timezone.now(),
        )

        registrar_primer_login(user, request=self._request(user))

        self.assertFalse(
            PublicAnalyticsEvent.objects.filter(
                event_type=PublicAnalyticsEvent.EVENT_FIRST_LOGIN
            ).exists()
        )

    def test_checkpoint_lease_has_single_live_owner(self):
        migration = importlib.import_module(
            "taller.migrations.0183_backfill_public_analytics_sessions"
        )
        checkpoint, _ = PublicAnalyticsBackfillCheckpoint.objects.update_or_create(
            key=migration.CHECKPOINT_KEY,
            defaults={
                "status": migration.CHECKPOINT_READY,
                "captured_at": timezone.now(),
                "owner_token": None,
                "lease_expires_at": None,
            },
        )

        owned, token = migration._acquire_lease(
            PublicAnalyticsBackfillCheckpoint,
            now=timezone.now(),
            token="owner-one",
        )
        self.assertEqual(owned.pk, checkpoint.pk)
        with self.assertRaises(migration.LeaseBusy):
            migration._acquire_lease(
                PublicAnalyticsBackfillCheckpoint,
                now=timezone.now(),
                token="owner-two",
            )
        checkpoint.refresh_from_db()
        self.assertEqual(checkpoint.owner_token, token)
        self.assertEqual(checkpoint.status, migration.CHECKPOINT_RUNNING)

    def test_legacy_event_gets_session_and_canonical_mapping(self):
        migration = importlib.import_module(
            "taller.migrations.0183_backfill_public_analytics_sessions"
        )
        created_at = timezone.now() - timedelta(days=1)
        event = PublicAnalyticsEvent.objects.create(
            event_type=PublicAnalyticsEvent.EVENT_SIGNUP_START,
            session_key=" legacy-session ",
            visitor_hash="bad",
            path="/cl/es/signup/",
            created_at=created_at,
            metadata={},
        )
        counters = migration._new_counters()
        changed = migration._process_group(
            PublicAnalyticsEvent,
            PublicPageView,
            PublicAnalyticsSession,
            "key:legacy-session",
            [event],
            [],
            counters,
        )

        self.assertTrue(changed)
        event.refresh_from_db()
        self.assertEqual(event.event_type, PublicAnalyticsEvent.EVENT_SIGNUP_STARTED)
        self.assertIsNotNone(event.session_id)
        self.assertEqual(event.dedupe_key, f"legacy-event-{event.pk}")
        self.assertTrue(event.metadata["_legacy_reconstruction"]["ledger_digest"])

    def test_related_event_and_pageview_with_different_keys_stay_intact(self):
        migration = importlib.import_module(
            "taller.migrations.0183_backfill_public_analytics_sessions"
        )
        page = PublicPageView.objects.create(
            path="/cl/es/landing/",
            page_type=PublicPageView.PAGE_LANDING,
            visitor_hash="a" * 64,
            session_key="A",
            created_at=timezone.now(),
        )
        event = PublicAnalyticsEvent.objects.create(
            event_type=PublicAnalyticsEvent.EVENT_SIGNUP_START,
            page_view=page,
            session_key="B",
            visitor_hash="b" * 64,
            created_at=timezone.now(),
            metadata={},
        )
        counters = migration._new_counters()

        migration._process_key_groups(
            PublicAnalyticsEvent,
            PublicPageView,
            PublicAnalyticsSession,
            counters,
            event_cutoff_pk=event.pk,
            pageview_cutoff_pk=page.pk,
        )

        page.refresh_from_db()
        event.refresh_from_db()
        self.assertIsNone(page.public_session_id)
        self.assertIsNone(event.session_id)
        self.assertFalse(event.metadata.get("_legacy_reconstruction"))
        self.assertEqual(PublicAnalyticsSession.objects.count(), 0)
