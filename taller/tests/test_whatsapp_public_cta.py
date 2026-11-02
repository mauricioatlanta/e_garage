from django.test import Client, TestCase, override_settings

from taller.services.country_localization import get_whatsapp_cta_context


@override_settings(
    WHATSAPP_CONTACT_NUMBER="56912345678",
    PUBLIC_ANALYTICS_HASH_KEY="test-public-analytics-key",
)
class WhatsAppPublicCtaTests(TestCase):
    def test_chile_tire_message_uses_local_rubro_and_number(self):
        cta = get_whatsapp_cta_context("cl", "tire")

        self.assertEqual(cta["number"], "56912345678")
        self.assertEqual(cta["rubro_local"], "Vulcanización")
        self.assertIn("Vulcanizaci%C3%B3n", cta["url"])
        self.assertIn("Chile", cta["message"])

    def test_brazil_copy_is_portuguese(self):
        cta = get_whatsapp_cta_context("br", "parts")

        self.assertEqual(cta["button_label"], "📲 Testar demo grátis no WhatsApp")
        self.assertEqual(cta["rubro_local"], "Autopeças")
        self.assertIn("Gostaria de testar", cta["message"])

    def test_us_english_copy_is_english(self):
        cta = get_whatsapp_cta_context("us_en", "workshop")

        self.assertEqual(cta["button_label"], "📲 Try Free Demo on WhatsApp")
        self.assertEqual(cta["rubro_local"], "auto shop")
        self.assertIn("in the US", cta["message"])

    def test_country_hub_renders_whatsapp_cta(self):
        response = Client().get("/mx/", HTTP_HOST="egarage.cl", HTTP_USER_AGENT="Mozilla/5.0")
        html = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn("Pedir acceso sin costo", html)
        self.assertIn("data-event=\"cta_whatsapp_click\"", html)
        self.assertIn("wa.me/56912345678", html)

    def test_vertical_landing_renders_local_whatsapp_cta(self):
        response = Client().get(
            "/ar/gomeria/",
            HTTP_HOST="egarage.cl",
            HTTP_USER_AGENT="Mozilla/5.0",
        )
        html = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn("Probá la demo gratis por WhatsApp", html)
        self.assertIn("Gomer%C3%ADa", html)
        self.assertIn("data-vertical=\"tire\"", html)
