from django.core.management.base import BaseCommand
from products.models import Product, PackagingMaterial
from bmr.models import EquipmentEntry


class Command(BaseCommand):
    help = 'Seed EquipmentEntry and PackagingMaterial rows for MCG CREAM (ointment, id=7)'

    def add_arguments(self, parser):
        parser.add_argument('--overwrite', action='store_true', help='Delete existing rows before seeding')

    def handle(self, *args, **options):
        try:
            product = Product.objects.get(pk=7)
        except Product.DoesNotExist:
            self.stderr.write('Product id=7 not found.')
            return

        if options['overwrite']:
            EquipmentEntry.objects.filter(product=product).delete()
            PackagingMaterial.objects.filter(product=product).delete()
            self.stdout.write('Deleted existing rows for product id=7.')

        # ── Equipment entries ────────────────────────────────────────────────
        equipment = [
            # phase, order, name, equipment_id
            ('dispensing', 1,  'Weighing Balance',               'B-46'),
            ('dispensing', 2,  'Weighing Balance',               'G-28'),
            ('dispensing', 3,  'Weighing Balance',               'B-59'),
            ('dispensing', 4,  'RLAF Booth',                     'LAF-01'),
            ('dispensing', 5,  'RLAF Booth',                     'LAF-05'),
            ('mixing',     1,  'Planetary Mixer',                'ON-01'),
            ('mixing',     2,  'Colloidal Mill',                 'ON-04'),
            ('tube_filling', 1, 'Tube Filling and Crimping Machine', 'ON-03'),
            ('tube_filling', 2, 'Electronic Balance',            'B-47'),
        ]
        eq_created = 0
        for phase, order, name, eq_id in equipment:
            _, created = EquipmentEntry.objects.get_or_create(
                product=product, phase=phase, order=order,
                defaults={'equipment_name': name, 'equipment_id': eq_id},
            )
            if created:
                eq_created += 1

        # ── Packaging materials (pack_type='bulk' → used by packaging_materials_bulk context key) ──
        packaging = [
            # order, item_code, description, unit, pack_type
            (1,  '1MCG1CT', 'MCG CREAM 15g CARTONS (TRADE)',       'PCS',  'bulk'),
            (2,  '4MCG1CT', 'MCG CREAM 15g TUBES (TRADE)',         'PCS',  'bulk'),
            (3,  '1MCG1CT', 'MCG CREAM 15g CARTONS (UG)',          'PCS',  'bulk'),
            (4,  '4MCG1CT', 'MCG CREAM 15g TUBES (UG)',            'PCS',  'bulk'),
            (5,  'SJJ2XF',  '400x15g Shipping Cartons',            'PCS',  'bulk'),
            (6,  'BPTPE2',  '2" BOPP Printed Packing Tape',        'PCS',  'bulk'),
            (7,  '9LDB810', '"8x10" HDPE Plain, Clear Bags',       'PCS',  'bulk'),
            (8,  'PIL MCG', 'MCG Patient Information Leaflets',     'PCS',  'bulk'),
        ]
        pkg_created = 0
        for order, code, desc, unit, pack_type in packaging:
            _, created = PackagingMaterial.objects.get_or_create(
                product=product,
                item_code=code,
                item_description=desc,
                defaults={'units': unit, 'pack_type': pack_type, 'order': order},
            )
            if created:
                pkg_created += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done. Created {eq_created} equipment entries, {pkg_created} packaging materials for {product.product_name}.'
        ))
