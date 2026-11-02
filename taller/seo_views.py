from xml.sax.saxutils import escape

from django.http import HttpResponse

from taller.country.engine import get_hub_landing_urls
from taller.country.hub import COUNTRY_HUB


CANONICAL_HOST = "https://egarage.cl"


def _canonical_public_urls():
    urls = [
        "/",
        "/cl/",
        "/ar/",
        "/pe/",
        "/mx/",
        "/ec/",
        "/ve/",
        "/br/",
        "/uy/es/",
        "/us/",
        "/us/en/",
        "/us/es/",
    ]

    for country_key in COUNTRY_HUB:
        landing_urls = get_hub_landing_urls(country_key)
        for path in landing_urls.values():
            if path not in urls:
                urls.append(path)

    return urls


def sitemap_xml(request):
    urls = _canonical_public_urls()

    body = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]

    for path in urls:
        loc = escape(f"{CANONICAL_HOST}{path}")
        body.append("  <url>")
        body.append(f"    <loc>{loc}</loc>")
        body.append("  </url>")

    body.append("</urlset>")

    return HttpResponse(
        "\n".join(body) + "\n",
        content_type="application/xml; charset=utf-8",
    )


def robots_txt(request):
    if getattr(request, "is_custom_domain", False):
        sitemap_url = f"https://{request.get_host()}/commerce/sitemap.xml"
    else:
        sitemap_url = "https://egarage.cl/sitemap.xml"
    body = f"""User-agent: *
Allow: /

Disallow: /admin/
Disallow: /accounts/
Disallow: /api/
Disallow: /analytics/
Disallow: /workspace/
Disallow: /*/workspace/
Disallow: /*/*/workspace/
Disallow: /*/dashboard/
Disallow: /*/*/dashboard/

Sitemap: {sitemap_url}
"""
    return HttpResponse(body, content_type="text/plain; charset=utf-8")
