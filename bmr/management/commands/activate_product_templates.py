"""
Activate exactly one BMRTemplate per product type.
Uses queryset.update() to bypass the save() signal.

Run:
    python manage.py activate_product_templates
"""
from django.core.management.base import BaseCommand
from bmr.models import BMRTemplate


class Command(BaseCommand):
    help = 'Activate one BMRTemplate per product type independently'

    def handle(self, *args, **options):
        PRODUCT_TYPES = ['ointment', 'capsule', 'tablet']

        for pt in PRODUCT_TYPES:
            tpls = BMRTemplate.objects.filter(product_type=pt).order_by('-updated_at')
            if not tpls.exists():
                self.stdout.write(self.style.WARNING(f'  No template for "{pt}" — skipping'))
                continue

            # Pick the most-recently-updated one as the active one
            best = tpls.first()

            # Deactivate all others of the same product_type using update() (no save() call)
            BMRTemplate.objects.filter(product_type=pt).exclude(pk=best.pk).update(is_active=False)
            # Activate the chosen template using update() (no save() call — avoids deactivating others)
            BMRTemplate.objects.filter(pk=best.pk).update(is_active=True)

            self.stdout.write(self.style.SUCCESS(
                f'  Activated: pk={best.pk}  "{best.name}"  product_type="{pt}"'
            ))

        self.stdout.write(self.style.SUCCESS('\nDone.'))
