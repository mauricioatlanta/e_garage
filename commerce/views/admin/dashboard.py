from django.shortcuts import render

from commerce.services.admin.brand_service import BrandService
from commerce.services.admin.category_service import CategoryService
from commerce.services.admin.product_service import ProductService
from commerce.views.admin.decorators import commerce_admin_required


@commerce_admin_required
def commerce_admin_dashboard(request):
    empresa = request.user.empresa
    product_stats = ProductService.stats(empresa)
    category_stats = CategoryService.stats(empresa)
    brand_summary = BrandService.summary(empresa)
    return render(request, "commerce/admin/dashboard.html", {
        "product_stats": product_stats,
        "category_stats": category_stats,
        "brand": brand_summary,
    })
