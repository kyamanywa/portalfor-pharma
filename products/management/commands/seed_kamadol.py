from django.core.management.base import BaseCommand
from products.models import Product, PackagingMaterial


class Command(BaseCommand):
    help = 'Seed Kamadol packaging materials into the database'

    def handle(self, *args, **options):
        try:
            kmd = Product.objects.get(id=13)
        except Product.DoesNotExist:
            kmd = Product.objects.filter(product_name__icontains='kamadol').first()
        if not kmd:
            self.stderr.write('Kamadol product not found')
            return

        PackagingMaterial.objects.filter(product=kmd).delete()

        blister = [
            ('KMD 203TB', 'Kamadol Tablets Aluminium Foil 203 x 0.25 mm (D/T)', 'Kg'),
            ('KMD 205TB', 'Kamadol Tablets Aluminium Foil 205 x 0.25 mm (D/T)', 'Kg'),
            ('PF 206M',   'PVC Clear Film 206 x 0.25mm (D/T)', 'Kg'),
            ('PF 210M',   'PVC Clear Film 210 x 0.25mm (D/T)', 'Kg'),
            ('KMD BC',    'Kamadol 10x10 Blister Cartons', 'PCS'),
            ('KMD DC',    'Kamadol 100x10x10 Blister Dispensers', 'PCS'),
            ('T150 100',  "Kamadol 10 x 10's Blister Shipping Cartons", 'PCS'),
            ('T24 1000',  "Kamadol 100x10x10's Blister Shipping Cartons", 'PCS'),
            ('BPTPE2',    '2" BOPP Printed Packing Tape', 'PCS'),
            ('PILKMD',    'Kamadol patient information leaflets', 'PCS'),
        ]
        bulk = [
            ('KMD3TJT', "Kamadol Tablets 500's labels (Trade)", 'PCS'),
            ('KMD4TJT', "Kamadol Tablets 1000's labels (Trade)", 'PCS'),
            ('KMD4TJU', "Kamadol Tablets 1000's labels (UG)", 'PCS'),
            ('PJ1KCC',  '1000 cc plastic jars with caps', 'PCS'),
            ('PJ500 C', '500 cc plastic jars with caps', 'PCS'),
            ('LDB810',  '8" x 10" HDPE plain, clear bags for 1000s', 'PCS'),
            ('LDB658',  '6.5 x 8" HDPE plain clear bags for 500s', 'PCS'),
            ('SJJ4XM',  '20 x 1000 cc shipping cartons', 'PCS'),
            ('SJJ3XM',  '40 x 500 cc shipping cartons', 'PCS'),
            ('BPTPE2',  '2" BOPP printed packing tape', 'PCS'),
            ('PILKMD',  'Kamadol patient information leaflet', 'PCS'),
        ]

        for i, (code, desc, unit) in enumerate(blister, 1):
            PackagingMaterial.objects.create(product=kmd, item_code=code, item_description=desc, units=unit, pack_type='blister', order=i)

        for i, (code, desc, unit) in enumerate(bulk, 1):
            PackagingMaterial.objects.create(product=kmd, item_code=code, item_description=desc, units=unit, pack_type='bulk', order=i)

        total = PackagingMaterial.objects.filter(product=kmd).count()
        self.stdout.write(self.style.SUCCESS(f'Created {total} packaging materials for {kmd.product_name}'))
