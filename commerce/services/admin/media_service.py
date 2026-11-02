from django.db import transaction
from django.shortcuts import get_object_or_404

from commerce.models import CommerceProduct, ProductImage


class MediaService:

    MAX_IMAGES = 4

    @staticmethod
    def add_image(commerce_product: CommerceProduct, file, alt_text="", is_primary=False):
        existing = commerce_product.images.count()
        if existing >= MediaService.MAX_IMAGES:
            raise ValueError(f"Máximo {MediaService.MAX_IMAGES} imágenes por producto.")
        used_positions = set(
            commerce_product.images.values_list("position", flat=True)
        )
        position = next(p for p in range(1, MediaService.MAX_IMAGES + 1) if p not in used_positions)
        with transaction.atomic():
            if is_primary:
                commerce_product.images.filter(is_primary=True).update(is_primary=False)
            return ProductImage.objects.create(
                commerce_product=commerce_product,
                image=file,
                alt_text=alt_text,
                is_primary=is_primary or existing == 0,
                position=position,
            )

    @staticmethod
    def delete_image(commerce_product: CommerceProduct, image_pk: int):
        img = get_object_or_404(ProductImage, pk=image_pk, commerce_product=commerce_product)
        was_primary = img.is_primary
        img.delete()
        if was_primary:
            first = commerce_product.images.order_by("position").first()
            if first:
                first.is_primary = True
                first.save(update_fields=["is_primary"])

    @staticmethod
    def set_primary(commerce_product: CommerceProduct, image_pk: int):
        img = get_object_or_404(ProductImage, pk=image_pk, commerce_product=commerce_product)
        with transaction.atomic():
            commerce_product.images.filter(is_primary=True).update(is_primary=False)
            img.is_primary = True
            img.save(update_fields=["is_primary"])
        return img
