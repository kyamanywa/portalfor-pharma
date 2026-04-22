from django.core.management.base import BaseCommand
from products.models import Product, ProductIngredient


class Command(BaseCommand):
    help = 'Seed MCG cream raw material ingredients into the database'

    def handle(self, *args, **options):
        # Find the MCG product
        mcg = Product.objects.filter(product_name__icontains='MCG').first()
        if not mcg:
            mcg = Product.objects.filter(product_type='ointment').first()
        if not mcg:
            self.stderr.write('MCG / ointment product not found. Create it in admin first.')
            return

        self.stdout.write(f'Seeding ingredients for: {mcg.product_name} (id={mcg.id})')

        # Clear existing ingredients for this product
        deleted, _ = ProductIngredient.objects.filter(product=mcg).delete()
        self.stdout.write(f'Removed {deleted} existing ingredient(s).')

        # MCG Cream raw materials from the official BMR (KPI/MFR/038/00)
        # Page 1 has items 1-7, page 2 has items 8-10
        # name, item_code, ingredient_type, qty_per_unit (mg/g), overage, lot_count, uom
        ingredients = [
            # --- Page 1 items (order 1-7) ---
            ('Miconazole Nitrate BP',       'MCZ1NN', 'active',    '20.00',  '0.00', 1, 'mg/g'),
            ('Clobetasol Propionate BP',     'CBS1PN', 'active',    '0.50',   '0.00', 1, 'mg/g'),
            ('Gentamycin Sulphate BP',       'GTM1SN', 'active',    '1.00',   '0.00', 1, 'mg/g'),
            ('Cetostearyl Alcohol BP',       'CSA2XN', 'excipient', '117.04', '0.00', 1, 'mg/g'),
            ('Cetomacrogol 1000 BP',         'CMG2XN', 'excipient', '50.00',  '0.00', 1, 'mg/g'),
            ('Chlorocresol BP',              'CCS2XN', 'excipient', '5.00',   '0.00', 1, 'mg/g'),
            ('Sodium Acid Phosphate BP',     'SAH2PN', 'excipient', '1.20',   '0.00', 1, 'mg/g'),
            # --- Page 2 items (order 8-10) ---
            ('Light Liquid Paraffin BP',     'LIP2XN', 'excipient', '146.66', '0.00', 2, 'mg/g'),  # 2 lots
            ('White Soft Paraffin BP',       'WSP2XN', 'excipient', '332.00', '0.00', 1, 'mg/g'),
            ('Purified Water BP',            'PWT2XN', 'excipient', '326.60', '0.00', 1, 'mg/g'),
        ]

        created = 0
        for order, (name, code, ing_type, qty, overage, lots, uom) in enumerate(ingredients, start=1):
            ProductIngredient.objects.create(
                product=mcg,
                order=order,
                ingredient_name=name,
                item_code=code,
                ingredient_type=ing_type,
                quantity_per_unit=qty,
                overage=overage,
                lot_count=lots,
                unit_of_measure=uom,
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(
            f'Created {created} ingredients for {mcg.product_name}. '
            f'Total mg/g = {sum(float(r[3]) for r in ingredients):.2f}'
        ))
