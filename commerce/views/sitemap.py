from xml.sax.saxutils import escape

from django.http import Http404, HttpResponse

from commerce.models import CommerceCategory, CommerceProduct


def commerce_sitemap_xml(request):
    empresa = getattr(request, "empresa", None) or getattr(request, "commerce_empresa", None)
    if not empresa:
        raise Http404

    categories = CommerceCategory.objects.filter(empresa=empresa, is_active=True).order_by("name")
    products = CommerceProduct.objects.filter(empresa=empresa, is_publishable=True).order_by("slug")

    body = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        "  <url>",
        f"    <loc>{escape(request.build_absolute_uri('/commerce/'))}</loc>",
        "  </url>",
    ]

    for cat in categories:
        body.append("  <url>")
        body.append(f"    <loc>{escape(request.build_absolute_uri(cat.get_absolute_url()))}</loc>")
        body.append("  </url>")

    for product in products:
        body.append("  <url>")
        body.append(f"    <loc>{escape(request.build_absolute_uri(product.get_absolute_url()))}</loc>")
        body.append("  </url>")

    body.append("</urlset>")

    return HttpResponse(
        "\n".join(body) + "\n",
        content_type="application/xml; charset=utf-8",
    )
