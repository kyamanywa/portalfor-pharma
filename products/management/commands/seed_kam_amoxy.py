"""
Seed/update KAM AMOXY Capsules product with exact data from the official BMR PDF.

Run:
    python manage.py seed_kam_amoxy
    python manage.py seed_kam_amoxy --force   (re-sets ingredients even if they exist)
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Seed KAM AMOXY Capsules (pk=16) with exact data from BMR PDF version 03"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Delete and recreate all ingredients (otherwise only adds missing ones).",
        )

    def handle(self, *args, **options):
        from products.models import Product, ProductIngredient, PackagingMaterial

        # ── Find product ─────────────────────────────────────────────────────────
        product = (
            Product.objects.filter(pk=16).first()
            or Product.objects.filter(product_name__icontains="KAM AMOXY").first()
        )
        if not product:
            self.stderr.write(self.style.ERROR("KAM AMOXY product not found in database."))
            return

        with transaction.atomic():
            # ── 1. Update product header fields from PDF ──────────────────────────
            product.product_name          = "KAM AMOXY CAPSULES"
            product.generic_name          = "Amoxicillin Capsules BP 250mg"
            product.mfr_number            = "KPI/MFR/033/00"
            product.bmr_revision_no       = "03"
            product.reference_sop_number  = "QAD/022/01"
            product.standard_batch_size   = Decimal("500000")
            product.batch_size_unit       = "capsules"

            # Pack sizes (PDF page 1)
            product.pack_size_1_code        = "KMX1CB"
            product.pack_size_1_description = "10x10 Blisters"
            product.pack_size_2_code        = "KMX2CB"
            product.pack_size_2_description = "1000's"
            product.pack_size_3_code        = ""
            product.pack_size_3_description = ""
            product.pack_size_4_code        = ""
            product.pack_size_4_description = ""

            # Product details (PDF page 3)
            product.label_claim = (
                "Each Kam Amoxy Capsule Contains: Amoxicillin Trihydrate BP equivalent to "
                "Amoxicillin 250mg"
            )
            product.color_description = (
                "Cap: Maroon printed on 'KPI logo' / UG & KPI logo in black. "
                "Body: Peach printed on 'KAM AMOXY 250' in black"
            )
            product.shelf_life_years     = Decimal("3")
            product.storage_conditions   = (
                "Store in a cool & dry place. Protect from direct light, heat and moisture."
            )
            product.mfg_license_number   = "NDA/MAL/HDP/8089"
            product.brand_name           = "Kam Amoxy"
            product.market_type          = "Domestic/Local"
            product.average_weight_uncoated = Decimal("320.0")   # 320.0 mg net content
            product.dissolution_spec     = "NA"
            product.assay_min_percentage = Decimal("92.5")   # PDF: 92.5% to 110.0%
            product.assay_max_percentage = Decimal("110.0")
            product.disintegration_time_max = Decimal("30")  # NMT 30 min (capsule filling IPQC)
            product.save()
            self.stdout.write(self.style.SUCCESS(
                f"Updated product: {product.product_name}  (pk={product.pk})"
            ))

            # ── 2. Ingredients ────────────────────────────────────────────────────
            if options["force"]:
                deleted, _ = ProductIngredient.objects.filter(product=product).delete()
                self.stdout.write(self.style.WARNING(f"Deleted {deleted} existing ingredients."))

            # Data from PDF pages 1–2:
            # order, name, item_code, qty_per_unit_mg, overage_mg, lot_count, uom, type
            ingredients_data = [
                (
                    1,
                    "Amoxicillin Trihydrate BP Compacted",
                    "AMX1TC",
                    Decimal("288.00"),
                    Decimal("2.00"),
                    1,
                    "mg/Capsule",
                    "active",
                ),
                (
                    2,
                    "Colloidal Silicone Dioxide BP (Aerosil 200)",
                    "AER2XN",
                    Decimal("2.00"),
                    Decimal("0.00"),
                    1,
                    "mg/Capsule",
                    "excipient",
                ),
                (
                    3,
                    "Lactose Monohydrate BP",
                    "LAC2MN",
                    Decimal("21.00"),
                    Decimal("0.00"),
                    1,
                    "mg/Capsule",
                    "excipient",
                ),
                (
                    4,
                    "Magnesium Stearate BP",
                    "MAG2SN",
                    Decimal("7.00"),
                    Decimal("0.00"),
                    1,
                    "mg/Capsule",
                    "excipient",
                ),
                # Page 2 — Capsule shells (measured in units, not mg)
                # 510,000 shells for 500,000 capsules (2% overage for fill process losses)
                (
                    5,
                    "Empty Hard Gelatin Shell # 1 Maroon/Peach Printed\nKAM AMOXY 250 (body), KPI (cap)",
                    "GMP5HN",
                    Decimal("510000"),   # total shells for the batch — treated as direct count
                    Decimal("0"),
                    1,
                    "units",             # signals non-mg to views.py
                    "excipient",
                ),
            ]

            created_count = 0
            for order, name, code, qty, overage, lots, uom, itype in ingredients_data:
                obj, created = ProductIngredient.objects.update_or_create(
                    product=product,
                    order=order,
                    defaults={
                        "ingredient_name":  name,
                        "item_code":        code,
                        "quantity_per_unit": qty,
                        "overage":          overage,
                        "lot_count":        lots,
                        "unit_of_measure":  uom,
                        "ingredient_type":  itype,
                    },
                )
                if created:
                    created_count += 1
                    self.stdout.write(f"  Created ingredient {order}: {name[:40]}")
                else:
                    self.stdout.write(f"  Updated ingredient {order}: {name[:40]}")

            self.stdout.write(self.style.SUCCESS(
                f"Ingredients done — {created_count} created, {len(ingredients_data) - created_count} updated."
            ))

            # ── 3. Packaging materials ────────────────────────────────────────────
            PackagingMaterial.objects.filter(product=product).delete()

            blister = [
                ("2AMX1CB", "Kam Amoxy Capsules Aluminium Foil", "Kg"),
                ("1AMX1CB", "Kam Amoxy Capsules 10x10 Blister Cartons", "Kg"),
                ("PF206MM", "PVC Clear Film 206x0.25mm", "Kg"),
                ("STB1XC",  "100x100 Capsule Blister Shipping Cartons", "Kg"),
                ("BPTPE2",  '2" BOPP Printed Packing Tape', "PCS"),
                ("PIL AMX", "Kam Amoxy patient information leaflet", "PCS"),
            ]
            bulk = [
                ("3AMX4UG", "Kam Amoxy capsules 1000's Labels (UG)", "PCS"),
                ("3AMX4CJ", "Kam Amoxy capsules 1000's Labels (Trade)", "PCS"),
                ("PJ1KCC",  "1000 cc plastic jars with caps", "PCS"),
                ("9LDB810", '8" x 10" HDPE plastic, clear bags', "PCS"),
                ("SJJ4XM",  "20 x 1000 capsules bulk shipping cartons", "PCS"),
                ("BPTPE2",  '2" BOPP Printed Packing Tape', "PCS"),
                ("PIL AMX", "Kam Amoxy patient information leaflet", "PCS"),
            ]

            for i, (code, desc, unit) in enumerate(blister, 1):
                PackagingMaterial.objects.create(
                    product=product, item_code=code, item_description=desc,
                    units=unit, pack_type="blister", order=i,
                )
            for i, (code, desc, unit) in enumerate(bulk, 1):
                PackagingMaterial.objects.create(
                    product=product, item_code=code, item_description=desc,
                    units=unit, pack_type="bulk", order=i,
                )

            pm_count = PackagingMaterial.objects.filter(product=product).count()
            self.stdout.write(self.style.SUCCESS(
                f"Packaging materials done — {pm_count} records created."
            ))

        self.stdout.write(self.style.SUCCESS("KAM AMOXY seed complete."))
