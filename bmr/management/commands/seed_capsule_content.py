"""
Seed the product-linked content tables for KAM AMOXY CAPSULES (product id=16).

Data sourced from the official Kampala Pharmaceutical Industries
Batch Manufacturing Record PDF (Amoxicillin Capsules 250mg).

Run:
    python manage.py seed_capsule_content
    python manage.py seed_capsule_content --overwrite   # delete & recreate
"""

from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Seed EquipmentEntry, YieldReconciliationRow, WeightRangeLimit for KAM AMOXY CAPSULES"

    def add_arguments(self, parser):
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Delete existing rows for this product and recreate from scratch.",
        )

    def handle(self, *args, **options):
        from products.models import Product
        from bmr.models import EquipmentEntry, YieldReconciliationRow, WeightRangeLimit

        try:
            product = Product.objects.get(pk=16)
        except Product.DoesNotExist:
            self.stderr.write(self.style.ERROR("Product id=16 (KAM AMOXY CAPSULES) not found."))
            return

        overwrite = options["overwrite"]

        with transaction.atomic():
            if overwrite:
                EquipmentEntry.objects.filter(product=product).delete()
                YieldReconciliationRow.objects.filter(product=product).delete()
                WeightRangeLimit.objects.filter(product=product).delete()
                self.stdout.write(self.style.WARNING("Deleted existing rows — recreating…"))

            self._seed_equipment(product, EquipmentEntry, overwrite)
            self._seed_yield_rows(product, YieldReconciliationRow, overwrite)
            self._seed_weight_limits(product, WeightRangeLimit, overwrite)

        self.stdout.write(self.style.SUCCESS(
            f"Done — seeded content for [{product.product_name}]"
        ))

    # ------------------------------------------------------------------
    # EQUIPMENT  (stored interleaved left/right so the |pairs filter
    # produces the correct 2-column table layout in the template)
    # ------------------------------------------------------------------
    def _seed_equipment(self, product, model, overwrite):

        # ── GENERAL EQUIPMENT LIST (Page 5, 12 rows × 2 cols = 24 slots) ──
        # Odd orders = LEFT column, Even orders = RIGHT column.
        # Empty equipment_name ("") = blank colspan cell in template.
        general = [
            (1,  "Multimill",                          "PN-09"),
            (2,  "Leak Test Machine",                  "QD-070"),
            (3,  "Double Cone Blender",                "PN-06"),
            (4,  "LAF Booth",                          "—"),
            (5,  "Mechanical Sifter",                  "PN-07"),
            (6,  "Weighing Scale",                     "—"),
            (7,  "Compression Machine",                "PN-35"),
            (8,  "Capsule Filling Machine",            "PN-37"),
            (9,  "Tablet Dedusting Machine",           "PN-30"),
            (10, "Capsule Mini Sorter",                "PN-44"),
            (11, "Tablet Dedusting Machine",           "PN-31"),
            (12, "Capsule Polishing Machine",          "PN-40"),
            (13, "Blister Packing Machine",            "P-04"),
            (14, "Capsule Loading Machine",            "PN-42"),
            (15, "Hardness Tester",                    "QD-082"),
            (16, "Strip Packing Machine",              "—"),
            (17, "Friabilator",                        "QD-080"),
            (18, "Vernier Caliper",                    "—"),
            (19, "Disintegration Tester Apparatus",    "QD-091"),
            (20, "",                                   ""),   # right = blank
            (21, "Electronic Moisture Balance",        "B-20"),
            (22, "",                                   ""),   # right = blank
            (23, "Electronic Balance",                 "B-33"),
            (24, "",                                   ""),   # right = blank
        ]

        # ── BLENDING / SIFTING EQUIPMENT (Page 9) ──
        blending = [
            (1, "Double Cone Blender",  "PN-06"),
            (2, "Multimill",            "PN-09"),
            (3, "Mechanical Sifter",    "PN-07"),
        ]

        # ── CAPSULE FILLING EQUIPMENT (Page 14, 6 items in 2 columns) ──
        capsule_filling = [
            (1, "ACG AF 90T Capsule Filling Machine", "PN-37"),
            (2, "Automatic Dust Unit (ADU)",          "PN-38"),
            (3, "Capsule Mini Sorter",                "PN-44"),
            (4, "Empty Capsule Sorter",               "PN-41"),
            (5, "Capsule Polishing Machine",          "PN-40"),
            (6, "Capsule Loading Machine",            "PN-42"),
        ]

        counts = {"general": 0, "blending": 0, "capsule_filling": 0}

        for phase, rows in [("general", general), ("blending", blending), ("capsule_filling", capsule_filling)]:
            if overwrite:
                # already deleted above
                for order, name, eid in rows:
                    model.objects.create(product=product, phase=phase,
                                         equipment_name=name, equipment_id=eid, order=order)
                    counts[phase] += 1
            else:
                for order, name, eid in rows:
                    _, created = model.objects.get_or_create(
                        product=product, phase=phase, order=order,
                        defaults={"equipment_name": name, "equipment_id": eid},
                    )
                    if created:
                        counts[phase] += 1

        self.stdout.write(f"  EquipmentEntry — general:{counts['general']}  blending:{counts['blending']}  capsule_filling:{counts['capsule_filling']}")

    # ------------------------------------------------------------------
    # YIELD RECONCILIATION ROWS
    # ------------------------------------------------------------------
    def _seed_yield_rows(self, product, model, overwrite):

        blending = [
            (1, "A", "Theoretical Batch Size with respect to Dispensed Materials"),
            (2, "B", "Actual Quantities of Lubricated Granules"),
            (3, "C", "Sample Quantities (L.O.D / In-Process checks)"),
            (4, "D", "Validation Samples"),
            (5, "E", "Rejects (if any)"),
            (6, "F", "Total Actual Yield (B+C+D)"),
            (7, "G", "Unaccountable Losses [A\u2212(E+F)]"),
        ]

        capsule_filling = [
            (1, "A", "Weight of blend received (kg)"),
            (2, "B", "Actual Quantities of Capsules Filled (kg)"),
            (3, "C", "Number of Capsules (units)"),
            (4, "D", "Total weight of empty shells used (kg)"),
            (5, "E", "Sample Quantities (kg)"),
            (6, "F", "Validation Samples (kg)"),
            (7, "G", "Rejects (kg)"),
            (8, "H", "Total accounted for (B + E + F)"),
            (9, "I", "Theoretical Batch Size = (A + D)"),
        ]

        blistering = [
            (1, "A", "Theoretical Batch Size (Blisters) with respect to capsules received from sorting"),
            (2, "B", "Actual Quantities of Blisters"),
            (3, "C", "Sample Quantities (In-Process checks)"),
            (4, "D", "Validation Samples"),
            (5, "E", "Rejects (if any)"),
            (6, "F", "Total Actual Yield (B+C+D)"),
            (7, "G", "Unaccountable Losses [A\u2212(E+F)]"),
        ]

        counts = {}
        for phase, rows in [("blending", blending), ("capsule_filling", capsule_filling), ("blistering", blistering)]:
            counts[phase] = 0
            for order, key, label in rows:
                if overwrite:
                    model.objects.create(product=product, phase=phase,
                                         row_key=key, label=label, order=order)
                    counts[phase] += 1
                else:
                    _, created = model.objects.get_or_create(
                        product=product, phase=phase, order=order,
                        defaults={"row_key": key, "label": label},
                    )
                    if created:
                        counts[phase] += 1

        self.stdout.write(f"  YieldReconciliationRow — blending:{counts['blending']}  capsule_filling:{counts['capsule_filling']}  blistering:{counts['blistering']}")

    # ------------------------------------------------------------------
    # WEIGHT RANGE LIMITS (Capsule Filling, Page 14)
    # ------------------------------------------------------------------
    def _seed_weight_limits(self, product, model, overwrite):

        rows = [
            # order, category, percent_of_target, tolerance_code, action, is_highlighted
            (1, ">105%",          ">105%", ">+T2", "Action",    False),
            (2, "105%",           "105%",  "+T2",  "Alert",     False),
            (3, "103%",           "103%",  "+T1",  "Good",      False),
            (4, "100% (320.00mg)","100%",  "Norm", "Very Good", True),   # target row (green)
            (5, "97%",            "97%",   "-T1",  "Good",      False),
            (6, "95%",            "95%",   "-T2",  "Alert",     False),
            (7, "<95%",           "<95%",  "<-T2", "Action",    False),
        ]

        count = 0
        for order, cat, pct, tol, action, highlighted in rows:
            if overwrite:
                model.objects.create(
                    product=product, phase="capsule_filling",
                    category=cat, percent_of_target=pct,
                    tolerance_code=tol, action=action,
                    is_highlighted=highlighted, order=order,
                )
                count += 1
            else:
                _, created = model.objects.get_or_create(
                    product=product, phase="capsule_filling", order=order,
                    defaults={
                        "category": cat, "percent_of_target": pct,
                        "tolerance_code": tol, "action": action,
                        "is_highlighted": highlighted,
                    },
                )
                if created:
                    count += 1

        self.stdout.write(f"  WeightRangeLimit — capsule_filling:{count}")
