from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from workflow.models import ProductTypeConfiguration

User = get_user_model()

class Command(BaseCommand):
    help = 'Seed initial product types into ProductTypeConfiguration table'

    def handle(self, *args, **options):
        # Get or create a system user for audit trail
        system_user, _ = User.objects.get_or_create(
            username='system',
            defaults={
                'email': 'system@pharma.local',
                'is_staff': True,
                'is_superuser': False,
            }
        )

        # Define base product types
        product_types = [
            {
                'product_type_key': 'tablet',
                'product_type_display': 'Tablet',
                'description': 'Tablet products including normal and type 2 variants',
                'default_packing_phase': 'blister_packing',
                'is_active': True,
            },
            {
                'product_type_key': 'capsule',
                'product_type_display': 'Capsule',
                'description': 'Capsule products with drying, blending, filling workflow',
                'default_packing_phase': 'filling',
                'is_active': True,
            },
            {
                'product_type_key': 'ointment',
                'product_type_display': 'Ointment',
                'description': 'Ointment products with mixing and tube filling workflow',
                'default_packing_phase': 'tube_filling',
                'is_active': True,
            },
        ]

        created_count = 0
        for pt in product_types:
            obj, created = ProductTypeConfiguration.objects.get_or_create(
                product_type_key=pt['product_type_key'],
                defaults={
                    'product_type_display': pt['product_type_display'],
                    'description': pt['description'],
                    'default_packing_phase': pt['default_packing_phase'],
                    'is_active': pt['is_active'],
                    'created_by': system_user,
                }
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created: {obj.product_type_display}')
                )
                created_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(f'⊘ Already exists: {obj.product_type_display}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Seeding complete. {created_count} new product types added.')
        )
