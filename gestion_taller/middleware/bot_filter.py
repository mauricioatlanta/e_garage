import logging
from django.http import HttpResponse

logger = logging.getLogger(__name__)


class BotFilterMiddleware:
    """
    Middleware to quickly reject common bot scanning attempts.
    Returns 404 early for known bot paths to reduce server load.
    """

    # Common WordPress/CMS vulnerability scanner paths
    BOT_PATHS = {
        "/wp-includes/",
        "/wp-content/",
        "/wordpress/",
        "/wp-admin/",
        "/wp-login.php",
        "/.env",
        "/phpMyAdmin/",
        "/phpmyadmin/",
        "/.git/",
        "/admin/config.php",
        "/xmlrpc.php",
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path.lower()

        # Quick check for bot paths
        for bot_path in self.BOT_PATHS:
            if bot_path in path:
                logger.info(
                    f"Bot scan blocked: {request.path} from {request.META.get('REMOTE_ADDR')}"
                )
                return HttpResponse(status=404)

        return self.get_response(request)
