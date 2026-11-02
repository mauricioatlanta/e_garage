from django.conf import settings


def analytics_context(request):
    return {
        "egarage_analytics_id": getattr(settings, "GOOGLE_ANALYTICS_ID", ""),
    }
