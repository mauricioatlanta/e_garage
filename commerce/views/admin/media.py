from django.shortcuts import render

from commerce.services.admin.media_dashboard import MediaDashboardService
from commerce.views.admin.decorators import commerce_admin_required


@commerce_admin_required
def media_library(request):
    empresa = request.user.empresa
    data = MediaDashboardService(empresa).summary()
    return render(request, "commerce/admin/media/library.html", {"lib": data})
