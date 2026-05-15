from datetime import datetime

from .version import APP_VERSION, COPYRIGHT_OWNER, COPYRIGHT_START_YEAR


def branding(request):
    current_year = datetime.now().year
    years = (
        f"{COPYRIGHT_START_YEAR}-{current_year}"
        if current_year > COPYRIGHT_START_YEAR
        else f"{current_year}"
    )
    return {
        "APP_VERSION": APP_VERSION,
        "COPYRIGHT_TEXT": f"© {years} {COPYRIGHT_OWNER}. Todos los derechos reservados.",
    }
