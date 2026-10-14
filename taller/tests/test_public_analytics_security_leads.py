import json

from django.test import RequestFactory, TestCase

from taller.models.abandoned_lead import AbandonedLead
from taller.models.public_page_view import PublicPageView
from taller.services.public_analytics import track_public_page
from taller.services.public_traffic_classifier import (
    is_canonical_public_host,
    is_probable_non_human_request,
)
from taller.views.public_analytics_events import public_signup_lead


class PublicAnalyticsSecurityLeadTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_classifier_rejects_ip_host_scanner_path_and_scanner_ua(self):
        ip_request = self.factory.get("/", HTTP_HOST="159.223.200.106")
        scan_request = self.factory.get("/wp-admin/", HTTP_HOST="egarage.cl")
        ua_request = self.factory.get("/", HTTP_HOST="egarage.cl", HTTP_USER_AGENT="curl/8.1")

        self.assertFalse(is_canonical_public_host("159.223.200.106"))
        self.assertTrue(is_probable_non_human_request(ip_request, "Mozilla/5.0"))
        self.assertTrue(is_probable_non_human_request(scan_request, "Mozilla/5.0"))
        self.assertTrue(is_probable_non_human_request(ua_request, "curl/8.1"))

    def test_track_public_page_marks_ip_host_as_bot(self):
        request = self.factory.get(
            "/cl/desarmadurias/",
            HTTP_HOST="159.223.200.106",
            HTTP_USER_AGENT="Mozilla/5.0",
        )

        page_view = track_public_page(request, page_type=PublicPageView.PAGE_LANDING, country="cl")

        self.assertIsNotNone(page_view)
        self.assertTrue(page_view.is_bot)
        self.assertEqual(page_view.host, "159.223.200.106")

    def test_public_signup_lead_creates_or_updates_lead(self):
        payload = {
            "nombre": "Ana Repuestos",
            "email": "ana@example.com",
            "whatsapp": "+56 9 1234 5678",
            "rubro": "CASA_REPUESTOS",
            "pais": "CL",
        }
        request = self.factory.post(
            "/analytics/public/lead/",
            data=json.dumps(payload),
            content_type="application/json",
            REMOTE_ADDR="203.0.113.10",
            HTTP_HOST="egarage.cl",
        )

        response = public_signup_lead(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(AbandonedLead.objects.count(), 1)
        lead = AbandonedLead.objects.get()
        self.assertEqual(lead.email, "ana@example.com")
        self.assertEqual(lead.pais, "CL")
        self.assertEqual(lead.whatsapp_url, "https://wa.me/56912345678")
