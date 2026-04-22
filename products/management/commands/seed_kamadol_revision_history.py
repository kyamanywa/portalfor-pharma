from django.core.management.base import BaseCommand
from products.models import Product, ProductRevisionHistory


REVISION_DATA = [
    {
        'revision_no': '01',
        'changes_incorporated': (
            "1. KPI new logo to be incorporated\n"
            "2. The provision for BMR preparation, Review, Approval and Authorization have been introduced on the Master Formula Page(s).\n"
            "3. An Index has been introduced.\n"
            "4. The Abbreviations used in the BMR have been defined in full.\n"
            "5. List Of Equipment & Instruments used in product manufactured have been summarized.\n"
            "6. Line Clearance for Dispensing previously missing has been introduced.\n"
            "7. Documentation of First Drying, Second Drying, and Final Drying have been split and captured independently, and Milling activities including Sieves used plus LOD data are also being documented at granulation. Identity of the FBD used to dry a particular Lot has been captured.\n"
            "8. In-process Quality Control and Assurance (IPQC/IPQA) reports for both Production and QA at all stages (as appropriate) have been incorporated.\n"
            "9. Initial Compression Machine Setting instructions, Initial Dies and Punches Checking Record, Initial Individual Weight Records as per number of Punches/Stations of the Compression machine have been introduced/Captured."
        ),
        'reason_of_change': (
            "To improve on clarity of the BMR.\n"
            "To match up with the current practices."
        ),
        'effective_date': '',
        'order': 1,
    },
    {
        'revision_no': '02',
        'changes_incorporated': (
            "1. To eliminate duplication in the BMR header, introduce page breaks for different process steps and include MFR numbers in the BMR.\n"
            "2. To include the Line Clearance for Inspection and Sorting of Blisters/Strips and the Secondary Packing Procedure."
        ),
        'reason_of_change': (
            "To improve coherence of the BMR.\n"
            "To ensure maximum elimination of blister/Strip defects before packing."
        ),
        'effective_date': '',
        'order': 2,
    },
    {
        'revision_no': '03',
        'changes_incorporated': (
            "1. Batch Release sheet revised to ensure that batch release is Authorized by the Company Pharmacist/Pharmacist In-Charge.\n"
            "2. Shipper weight verification record introduced.\n"
            "3. Packaging Material Requisition Sheet incorporated in the BMR."
        ),
        'reason_of_change': (
            "To comply with regulatory requirements for batch release.\n"
            "To eliminate the risk of having less or more product quantity in a shipper."
        ),
        'effective_date': '',
        'order': 3,
    },
]


class Command(BaseCommand):
    help = 'Seed KAMADOL BMR revision history (from THE REVISED KAMADOL BMR-VERSION 03.pdf, page 59)'

    def handle(self, *args, **options):
        kmd = (
            Product.objects.filter(product_name__icontains='kamadol').first()
            or Product.objects.filter(id=13).first()
        )
        if not kmd:
            self.stderr.write(self.style.ERROR('KAMADOL product not found'))
            return

        existing = ProductRevisionHistory.objects.filter(product=kmd).count()
        if existing:
            self.stdout.write(
                self.style.WARNING(
                    f'{existing} revision entries already exist for {kmd.product_name}. '
                    'Deleting and re-seeding...'
                )
            )
            ProductRevisionHistory.objects.filter(product=kmd).delete()

        for entry in REVISION_DATA:
            ProductRevisionHistory.objects.create(product=kmd, **entry)

        total = ProductRevisionHistory.objects.filter(product=kmd).count()
        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded {total} revision history entries for {kmd.product_name}'
            )
        )
