from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render

from commerce.forms.category import CommerceCategoryForm
from commerce.services.admin.category_service import CategoryService
from commerce.views.admin.decorators import commerce_admin_required


@commerce_admin_required
def category_list(request):
    empresa = request.user.empresa
    roots = CategoryService.list_tree(empresa)
    stats = CategoryService.stats(empresa)
    return render(request, "commerce/admin/categories/list.html", {
        "roots": roots,
        "stats": stats,
    })


@commerce_admin_required
def category_create(request):
    empresa = request.user.empresa
    if request.method == "POST":
        form = CommerceCategoryForm(request.POST, request.FILES, empresa=empresa)
        if form.is_valid():
            CategoryService.create(empresa, form)
            messages.success(request, "Categoría creada correctamente.")
            return redirect("commerce:admin_category_list")
    else:
        form = CommerceCategoryForm(empresa=empresa)
    return render(request, "commerce/admin/categories/form.html", {
        "form": form,
        "action": "Crear",
    })


@commerce_admin_required
def category_edit(request, pk):
    empresa = request.user.empresa
    category = CategoryService.get(empresa, pk)
    if request.method == "POST":
        form = CommerceCategoryForm(request.POST, request.FILES, instance=category, empresa=empresa)
        if form.is_valid():
            CategoryService.save_form(form)
            messages.success(request, "Categoría actualizada.")
            return redirect("commerce:admin_category_list")
    else:
        form = CommerceCategoryForm(instance=category, empresa=empresa)
    return render(request, "commerce/admin/categories/form.html", {
        "form": form,
        "category": category,
        "action": "Editar",
    })


@commerce_admin_required
def category_toggle_active(request, pk):
    if request.method != "POST":
        return JsonResponse({"error": "POST requerido"}, status=405)
    empresa = request.user.empresa
    cat = CategoryService.toggle_active(empresa, pk)
    return JsonResponse({"is_active": cat.is_active, "pk": cat.pk})


@commerce_admin_required
def category_delete(request, pk):
    if request.method != "POST":
        return JsonResponse({"error": "POST requerido"}, status=405)
    empresa = request.user.empresa
    try:
        CategoryService.delete(empresa, pk)
        messages.success(request, "Categoría eliminada.")
    except ValueError as e:
        messages.error(request, str(e))
    return redirect("commerce:admin_category_list")
