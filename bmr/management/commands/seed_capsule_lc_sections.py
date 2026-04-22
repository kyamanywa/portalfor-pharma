"""
Seed LC (Line Clearance) sections for bmr_capsule.html's dynamic template rendering.

Creates BMRTemplateSection + BMRTemplateField rows matching the exact text
displayed in bmr_capsule.html.  The template checks
bmr_template_sections_by_phase.{PHASE_KEY} — if found, it renders from DB;
otherwise it falls back to the hardcoded HTML.

Run:
    python manage.py seed_capsule_lc_sections
    python manage.py seed_capsule_lc_sections --overwrite
"""

from django.core.management.base import BaseCommand
from django.db import transaction


# ─── Exact item text as shown in bmr_capsule.html ────────────────────────────

LC_DATA = {
    # key: list of (order, label) tuples
    "dispensing_beginning": [
        (1,  "Area cleaning is done as per SOP."),
        (2,  "Ensure the absence of batch documents, labels, materials or remnants of previous product or batch."),
        (3,  "Ensure availability of the BMR for the in-coming batch and Verify that ALL materials and facilities "
             "for new batch are available, labeled and identified."),
        (4,  "Gowning and de-gowning procedure is followed."),
        (5,  "Dispensing Room, Dispensing booth, Balances and dispensing tools are clean and have status as ready for use."),
        (6,  "Clean scoops, containers and poly bags are available for dispensing as per SOP."),
        (7,  "Manometer reading of dispensing booth RLAF is within the required limit. Actual Manometer reading: ___"),
        (8,  "Balance Calibration carried out before starting dispensing."),
        (9,  "Verify the release status & retest validity period of each material."),
        (10, "Ensure Environmental conditions are met as per SOP. "
             "Temperature NMT 28°C ___ Relative Humidity (40-65)% ___"),
        (11, "Ensure that the RLAF is started 15 minutes before start of the dispensing activities."),
    ],
    "dispensing_ending": [
        (1, "All material from current product have been removed."),
        (2, "All facilities have been cleaned and labeled."),
        (3, "The area has been cleaned and labeled."),
        (4, "All paperwork for the current batch has been completed."),
        (5, "Reconciliation of current batch has been done."),
        (6, "Ensure that utensils and accessories from previous operations have been removed."),
    ],

    "blending_beginning": [
        (1, "Area cleaning as per SOP."),
        (2, "Ensure that all the previous product containers, material, and labels are removed from the manufacturing area."),
        (3, "Gowning procedure is followed."),
        (4, "Ensure that status board is displayed with mentioning Product Name, Batch No, B. Size, "
            "Mfg. Date, Exp.Date & Status with sign & date."),
        (5, "Check the proper cleanliness of the Air Supply and Return grills."),
        (6, "Ensure that the Vibrosifter sieves, Double Cone Blender, Scoops etc. are cleaned."),
        (7, "Check and ensure that Balance Calibration & Verification records are updated."),
        (8, "Ensure Environmental conditions are met as per SOP. "
            "Temperature NMT 28°C ___ Relative Humidity (40-65)% ___"),
    ],
    "blending_ending": [
        (1, "All material from current product have been removed."),
        (2, "All facilities have been cleaned and labeled."),
        (3, "The area has been cleaned and labeled."),
        (4, "All paperwork for the current batch has been completed."),
        (5, "Reconciliation of current batch has been done."),
        (6, "Machine(s) has been checked for cleanliness."),
    ],

    "capsule_filling_beginning": [
        (1, "Area cleaning as per SOP."),
        (2, "Ensure that all the previous product containers, material, and labels are removed from the manufacturing area."),
        (3, "Gowning procedure is followed."),
        (4, "Ensure that status board is displayed with mentioning Product Name, Batch No, B. Size, "
            "Mfg. Date, Exp.Date & Status with sign & date."),
        (5, "Ensure the absence of batch documents, labels, materials or remnants of previous product "
            "or batch on each critical part."),
        (6, "Are the following parts of the capsule filling machine cleaned: "
            "Hopper/Feeder/Turret/Below the turret, Y-chute/Powder collection."),
        (7, "Check and ensure that Balance Calibration & Verification records are updated."),
        (8, "Ensure Environmental conditions are met as per SOP. "
            "Temperature NMT 28°C ___ Relative Humidity (40-65)% ___"),
    ],
    "capsule_filling_ending": [
        (1, "All material from current product have been removed."),
        (2, "All facilities have been cleaned and labeled."),
        (3, "The area has been cleaned and labeled."),
        (4, "All paperwork for the current batch has been completed."),
        (5, "Reconciliation of current batch has been done."),
        (6, "Machine(s) has been checked for cleanliness."),
    ],

    "capsule_inspection_beginning": [
        (1, "Area cleaning as per SOP."),
        (2, "Ensure that all the previous product containers, material, and labels are removed from the manufacturing area."),
        (3, "Gowning procedure is followed."),
        (4, "Ensure that status board is displayed with mentioning Product Name, Batch No, B. Size, "
            "Mfg. Date, Exp.Date & Status with sign & date."),
        (5, "Check the proper cleanliness of the Air Supply and Return grills and Air Conditioning System."),
        (6, "Ensure that the Vibrosifter sieves, Metal Detector, Deduster, Scoops etc. are cleaned."),
        (7, "Check and ensure that Balance Calibration & Verification records are updated."),
        (8, "Ensure Environmental conditions are met as per SOP. "
            "Temperature NMT 28°C ___ Relative Humidity (40 to 65%) ___"),
    ],
    "capsule_inspection_ending": [
        (1, "All material from current product have been removed."),
        (2, "All facilities have been cleaned and labeled."),
        (3, "The area has been cleaned and labeled."),
        (4, "All paperwork for the current batch has been completed."),
        (5, "Reconciliation of current batch has been done."),
        (6, "Machine(s) has been checked for cleanliness."),
    ],

    "packaging_beginning": [
        (1, "Area cleaning as per SOP."),
        (2, "Ensure that all the previous product containers, material, and labels are removed from the manufacturing area."),
        (3, "Gowning procedure is followed."),
        (4, "Ensure that status board is displayed with mentioning Product Name, Batch No, B. Size, "
            "Mfg. Date, Exp.Date & Status with sign & date."),
        (5, "Check the proper cleanliness of the Air Supply and Return grills and Air Conditioning System."),
        (6, "Ensure that the Vibrosifter sieves, Metal Detector, Deduster, Scoops etc. are cleaned."),
        (7, "Remove all the cartons, labels, strips, any material left over on the line and on the lower "
            "space of the conveyor belts."),
        (8, "Put an authorized overprinted specimen of strip/blister/cartons/Label/Tube in the BMR for "
            "ready reference."),
        (9, "Ensure Environmental conditions are met as per SOP. "
            "Temperature NMT 28°C ___ Relative Humidity (40 to 65%) ___"),
    ],
    "packaging_ending": [
        (1, "All material from current product have been removed."),
        (2, "All facilities have been cleaned and labeled."),
        (3, "The area has been cleaned and labeled."),
        (4, "All paperwork for the current batch has been completed."),
        (5, "Reconciliation of current batch has been done."),
        (6, "Stereos of previous product are submitted to production Supervisor."),
    ],

    # Secondary packaging continues numbering from primary: 10–18 beginning, 7–12 ending
    "secondary_packaging_beginning": [
        (10, "Area cleaning as per SOP."),
        (11, "Ensure that all the previous product containers, material, and labels are removed from "
             "the manufacturing area."),
        (12, "Gowning procedure is followed."),
        (13, "Ensure that status board is displayed with Product Name, Batch No, B.Size, "
             "Mfg.Date, Exp.Date & Status."),
        (14, "Check the proper cleanliness of the Air Supply and Return grills and Air Conditioning System."),
        (15, "Ensure that the Vibrosifter sieves, Metal Detector, Deduster, Scoops etc. are cleaned."),
        (16, "Remove all the cartons, labels, strips, any material left over on the line and on the lower "
             "space of the conveyor belts."),
        (17, "Put an authorized overprinted specimen of strip/blister/cartons/Label/Tube in the BMR for "
             "ready reference."),
        (18, "Environmental conditions: Temp NMT 28°C __ Relative Humidity (40-65)% __"),
    ],
    "secondary_packaging_ending": [
        (7,  "All material from current product have been removed."),
        (8,  "All facilities have been cleaned and labeled."),
        (9,  "The area has been cleaned and labeled."),
        (10, "All paperwork for the current batch has been completed."),
        (11, "Reconciliation of current batch has been done."),
        (12, "Stereos of previous product are submitted to production Supervisor."),
    ],
}

# Human-readable title for each section (shown in admin)
SECTION_TITLES = {
    "dispensing_beginning":              "Dispensing LC — Beginning Activities",
    "dispensing_ending":                 "Dispensing LC — Ending Activities",
    "blending_beginning":                "Blending/Lubrication LC — Beginning Activities",
    "blending_ending":                   "Blending/Lubrication LC — Ending Activities",
    "capsule_filling_beginning":         "Capsule Filling LC — Beginning Activities",
    "capsule_filling_ending":            "Capsule Filling LC — Ending Activities",
    "capsule_inspection_beginning":      "Capsule Inspection & Sorting LC — Beginning Activities",
    "capsule_inspection_ending":         "Capsule Inspection & Sorting LC — Ending Activities",
    "packaging_beginning":               "Packaging LC — Beginning Activities",
    "packaging_ending":                  "Packaging LC — Ending Activities",
    "secondary_packaging_beginning":     "Secondary Packaging LC — Beginning Activities (10–18)",
    "secondary_packaging_ending":        "Secondary Packaging LC — Ending Activities (7–12)",
}

# Map each phase to its BMR page number (informational only)
SECTION_PAGES = {
    "dispensing_beginning": 7,  "dispensing_ending": 7,
    "blending_beginning": 8,    "blending_ending": 8,
    "capsule_filling_beginning": 13, "capsule_filling_ending": 13,
    "capsule_inspection_beginning": 24, "capsule_inspection_ending": 24,
    "packaging_beginning": 28,  "packaging_ending": 28,
    "secondary_packaging_beginning": 36, "secondary_packaging_ending": 36,
}


class Command(BaseCommand):
    help = (
        "Seed Line Clearance sections (BMRTemplateSection + BMRTemplateField) "
        "for bmr_capsule.html's dynamic template rendering."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Delete existing LC sections for the capsule template and recreate.",
        )

    def handle(self, *args, **options):
        from bmr.models import BMRTemplate
        from bmr.template_models import BMRTemplateSection, BMRTemplateField

        overwrite = options["overwrite"]

        with transaction.atomic():
            # ── Find or create the capsule template ──────────────────────────
            template = BMRTemplate.objects.filter(product_type="capsule").first()
            if template is None:
                template = BMRTemplate.objects.create(
                    name="Capsule BMR Template (LC Sections)",
                    product_type="capsule",
                    description=(
                        "Auto-created by seed_capsule_lc_sections. "
                        "Holds line clearance sections for bmr_capsule.html dynamic rendering."
                    ),
                    is_active=False,
                )
                self.stdout.write(self.style.SUCCESS(f"Created new capsule BMRTemplate pk={template.pk}"))
            else:
                self.stdout.write(self.style.NOTICE(f"Using existing capsule BMRTemplate pk={template.pk}: {template.name}"))

            if overwrite:
                deleted_sections = BMRTemplateSection.objects.filter(
                    template=template,
                    section_type="line_clearance",
                    phase_name__in=list(LC_DATA.keys()),
                ).delete()
                self.stdout.write(self.style.WARNING(f"Deleted {deleted_sections[0]} existing LC sections."))

            # ── Create sections + fields ──────────────────────────────────────
            sections_created = 0
            fields_created = 0

            for order_idx, (phase_key, items) in enumerate(LC_DATA.items()):
                # Skip if already exists (idempotent without --overwrite)
                if BMRTemplateSection.objects.filter(template=template, phase_name=phase_key).exists():
                    self.stdout.write(
                        self.style.NOTICE(f"  SKIP (exists): {phase_key}")
                    )
                    continue

                section = BMRTemplateSection.objects.create(
                    template=template,
                    title=SECTION_TITLES[phase_key],
                    section_type="line_clearance",
                    phase_name=phase_key,
                    order=order_idx + 1,
                    page_number=SECTION_PAGES[phase_key],
                    is_required=True,
                    is_visible=True,
                )
                sections_created += 1

                fields_to_create = [
                    BMRTemplateField(
                        section=section,
                        label=label,
                        order=item_order,
                        field_type="static_text",
                        is_required=False,
                    )
                    for item_order, label in items
                ]
                BMRTemplateField.objects.bulk_create(fields_to_create)
                fields_created += len(fields_to_create)

                self.stdout.write(
                    f"  Created section '{phase_key}' ({len(items)} items)"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone — {sections_created} sections, {fields_created} fields seeded."
            )
        )
        if sections_created == 0:
            self.stdout.write(
                self.style.NOTICE("All sections already existed. Use --overwrite to recreate.")
            )
