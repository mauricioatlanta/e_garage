import json

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render

from commerce.forms.product import CommerceProductAdminForm
from commerce.services.admin.media_service import MediaService
from commerce.services.admin.product_service import ProductService
from commerce.views.admin.decorators import commerce_admin_required


@commerce_admin_required
def product_list(request):
    empresa = request.user.empresa
    search = request.GET.get("q", "").strip()
    category_pk = request.GET.get("categoria") or None
    published_filter = request.GET.get("estado") or None
    page = request.GET.get("page", 1)

    page_obj = ProductService.list(
        empresa,
        search=search,
        category_pk=category_pk,
        published_filter=published_filter,
        page=page,
    )
    categories = ProductService.categories_for_select(empresa)
    stats = ProductService.stats(empresa)

    return render(request, "commerce/admin/products/list.html", {
        "page_obj": page_obj,
        "search": search,
        "category_pk": category_pk,
        "published_filter": published_filter,
        "categories": categories,
        "stats": stats,
    })


@commerce_admin_required
def product_edit(request, pk):
    empresa = request.user.empresa
    product = ProductService.get(empresa, pk)
    if request.method == "POST":
        if request.POST.get("_upload_image"):
            img_file = request.FILES.get("new_image")
            if img_file:
                try:
                    alt_text = request.POST.get("new_image_alt", "")
                    MediaService.add_image(product, img_file, alt_text=alt_text)
                    messages.success(request, "Imagen agregada.")
                except ValueError as e:
                    messages.error(request, str(e))
            return redirect("commerce:admin_product_edit", pk=pk)
        form = CommerceProductAdminForm(request.POST, request.FILES, instance=product, empresa=empresa)
        if form.is_valid():
            ProductService.save_form(form)
            messages.success(request, "Producto actualizado correctamente.")
            return redirect("commerce:admin_product_list")
    else:
        form = CommerceProductAdminForm(instance=product, empresa=empresa)
    return render(request, "commerce/admin/products/form.html", {
        "form": form,
        "product": product,
    })


@commerce_admin_required
def product_toggle_publishable(request, pk):
    if request.method != "POST":
        return JsonResponse({"error": "POST requerido"}, status=405)
    empresa = request.user.empresa
    product = ProductService.toggle_publishable(empresa, pk)
    return JsonResponse({"is_publishable": product.is_publishable, "pk": product.pk})


@commerce_admin_required
def product_bulk_action(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST requerido"}, status=405)
    empresa = request.user.empresa
    try:
        body = json.loads(request.body)
        action = body.get("action")
        pks = [int(p) for p in body.get("pks", [])]
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Payload inválido"}, status=400)

    if not pks:
        return JsonResponse({"error": "Sin productos seleccionados"}, status=400)

    if action == "publish":
        count = ProductService.bulk_set_publishable(empresa, pks, True)
        return JsonResponse({"updated": count, "action": "publish"})
    elif action == "unpublish":
        count = ProductService.bulk_set_publishable(empresa, pks, False)
        return JsonResponse({"updated": count, "action": "unpublish"})
    else:
        return JsonResponse({"error": f"Acción desconocida: {action}"}, status=400)


@commerce_admin_required
def product_image_delete(request, pk, image_pk):
    if request.method != "POST":
        return JsonResponse({"error": "POST requerido"}, status=405)
    empresa = request.user.empresa
    product = ProductService.get(empresa, pk)
    MediaService.delete_image(product, image_pk)
    return JsonResponse({"deleted": True})


@commerce_admin_required
def product_image_set_primary(request, pk, image_pk):
    if request.method != "POST":
        return JsonResponse({"error": "POST requerido"}, status=405)
    empresa = request.user.empresa
    product = ProductService.get(empresa, pk)
    MediaService.set_primary(product, image_pk)
    return JsonResponse({"primary": image_pk})
