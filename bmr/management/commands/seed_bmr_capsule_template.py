"""
Management command to seed the Kam Amoxy Capsule BMR dynamic template.

Run:
    python manage.py seed_bmr_capsule_template
    python manage.py seed_bmr_capsule_template --overwrite
"""

from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Seed dynamic BMR template sections for Kam Amoxy Capsule (product_type='capsule')"

    def add_arguments(self, parser):
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Delete the existing capsule template and recreate from scratch.",
        )

    def handle(self, *args, **options):
        from bmr.models import BMRTemplate
        from bmr.template_models import BMRTemplateSection

        overwrite = options["overwrite"]

        with transaction.atomic():
            existing = BMRTemplate.objects.filter(product_type="capsule").first()
            if existing and overwrite:
                self.stdout.write(self.style.WARNING(f"Deleting existing template: {existing.name}"))
                existing.delete()
                existing = None

            if existing and not overwrite:
                self.stdout.write(
                    self.style.NOTICE(
                        f"Template already exists: '{existing.name}'  "
                        f"(use --overwrite to delete and recreate)"
                    )
                )
                return

            template = BMRTemplate.objects.create(
                name="Kam Amoxy Capsule BMR Template",
                product_type="capsule",
                description=(
                    "Dynamic BMR template for Kam Amoxy (Amoxicillin Trihydrate BP 500mg Capsules). "
                    "Covers material dispensing, drying, blending, post-blending QC, "
                    "capsule filling, sorting, blister packing, and secondary packaging."
                ),
                is_active=False,
            )
            self.stdout.write(self.style.SUCCESS(f"Created template: {template.name}  (pk={template.pk})"))

            sections = _build_sections(template)
            BMRTemplateSection.objects.bulk_create(sections)
            self.stdout.write(self.style.SUCCESS(f"Created {len(sections)} sections across all phases."))

        self.stdout.write(self.style.SUCCESS("Done — Kam Amoxy Capsule template seeded successfully."))


# ---------------------------------------------------------------------------
# Shared checklist text
# ---------------------------------------------------------------------------

_DISPENSING_LINE_CLEARANCE_BEGINNING = [
    "Area cleaning done as per SOP — no remnants of previous product / batch.",
    "Verify BMR availability and all materials are labeled and identified.",
    "Gowning procedure is followed.",
    "RLAF started minimum 15 minutes before dispensing activities.",
    "Manometer reading of RLAF is within the required limit.",
    "Balance calibration carried out and recorded before dispensing.",
    "Verify release status and retest validity of each raw material (AR numbers).",
    "Scoops, containers, poly bags and labels available and clean as per SOP.",
    "Environmental conditions met: Temp NMT 25°C, RH NMT 45%.",
]

_GENERIC_ENDING_ITEMS = [
    "Area / equipment cleaned and sanitised as per SOP after operation.",
    "All materials labeled, sealed and moved to correct storage.",
    "Waste disposed as per SOP.",
    "Logbooks and BMR entries completed and signed.",
    "Equipment status labels updated.",
    "Supervisor / QA reviewed and released the area.",
]

_DRYING_BEGINNING = [
    "Tray dryer / fluid bed dryer (FBD) cleaned and labeled 'CLEANED'.",
    "Trays, liners and scoops are clean and accounted for.",
    "Thermometer / thermocouple calibrated and in-date.",
    "BMR and weighing records available and verified.",
    "Temperature set-point recorded before loading.",
    "Environmental conditions within specification (Temp NMT 25°C, RH NMT 45%).",
]

_DRYING_ENDING = [
    "Dried material sampled for moisture content before transfer.",
    "Moisture content within specification (NMT 13.0% w/w) — result recorded.",
    "Dried material transferred to blending room in sealed, labeled containers.",
    "Dryer and trays cleaned as per SOP after use.",
    "Logbooks and BMR entries completed and signed.",
    "QA reviewed results and released for blending.",
]

_BLENDING_BEGINNING = [
    "Blender / V-blender cleaned and labeled 'CLEANED'.",
    "All blending equipment (scoops, spatulas, containers) clean and available.",
    "Dried Amoxicillin Trihydrate checked for correct AR — identified and labeled.",
    "Magnesium Stearate checked, weighed and identified.",
    "Environmental conditions within specification (Temp NMT 25°C, RH NMT 45%).",
    "BMR available and verified.",
]

_BLENDING_ENDING = [
    "Blended product transferred to capsule filling room in sealed, labeled containers.",
    "Blend uniformity sample submitted to QC.",
    "Blender cleaned as per SOP.",
    "Yield reconciliation completed in BMR.",
    "Logbooks and BMR entries completed and signed.",
    "QA reviewed and released blend for filling.",
]

_FILLING_BEGINNING = [
    "Capsule filling machine cleaned and labeled 'CLEANED'.",
    "Correct capsule shells (size, color, lot) verified and available.",
    "Blended product verified with correct BMR reference and AR number.",
    "IPC balances calibrated and ready.",
    "Polishing machine cleaned and ready.",
    "Environmental conditions within specification (Temp NMT 25°C, RH NMT 45%).",
    "BMR and IPC records available at filling station.",
]

_FILLING_ENDING = [
    "Filling machine cleaned after use as per SOP.",
    "Filled capsules transferred to sorting.",
    "Empty capsule shells reconciled and returned.",
    "Yield reconciliation completed in BMR.",
    "Logbooks and BMR entries completed and signed.",
    "QA reviewed and released filled capsules for sorting.",
]

_BLISTER_BEGINNING = [
    "Blister packing machine cleaned and labeled 'CLEANED'.",
    "Correct foil (aluminium) and base film (PVC/PVDC) checked and identified.",
    "Seal temperature and dwell time set as per batch specification.",
    "Printing (batch, mfg, exp date) set and QA-approved sample confirmed.",
    "BMR and IPC records available at packing station.",
    "Environmental conditions within specification.",
]

_BLISTER_ENDING = [
    "Blister machine cleaned as per SOP after end of batch.",
    "Rejected blisters counted and reconciled.",
    "Packed blisters transferred to secondary packing.",
    "Foil / film reconciled and remainders returned.",
    "Logbooks and BMR entries completed and signed.",
    "QA reviewed and released for secondary packing.",
]

# ---------------------------------------------------------------------------
# Process steps
# ---------------------------------------------------------------------------

_DRYING_STEPS = [
    {
        "num": "1",
        "desc": "Verify all dispensed Amoxicillin Trihydrate is present and correctly identified (AR No., weight per BMR).",
    },
    {
        "num": "2",
        "desc": "Spread Amoxicillin Trihydrate evenly on lined SS trays (NMT 2 cm depth per tray). "
                "Record number of trays used.",
    },
    {
        "num": "3",
        "desc": "Load trays into tray dryer. Set temperature to NMT 40°C. "
                "Run exhaust fan and record set temperature.",
    },
    {
        "num": "4",
        "desc": "Dry for minimum 2 hours. Check temperature every 30 minutes and record.",
    },
    {
        "num": "5",
        "desc": "After drying, sample from top / middle / bottom trays for Loss on Drying (LOD). "
                "Record moisture result. Specification: NMT 13.0% w/w (Amoxicillin Trihydrate BP).",
    },
    {
        "num": "6",
        "desc": "If moisture fails, continue drying and re-sample. "
                "Do NOT proceed to blending without passing LOD.",
    },
    {
        "num": "7",
        "desc": "Sieve dried material through 40-mesh sieve. Collect and label in sealed containers.",
    },
    {
        "num": "8",
        "desc": "Weigh sieved dry material and record. Transfer to blending room with proper labeling.",
    },
]

_BLENDING_STEPS = [
    {
        "num": "1",
        "desc": "Verify dried Amoxicillin Trihydrate is available and correctly identified.",
    },
    {
        "num": "2",
        "desc": "Sieve Magnesium Stearate (60 mesh) if not pre-sieved. Weigh the required quantity per BMR.",
    },
    {
        "num": "3",
        "desc": "Load Amoxicillin Trihydrate into V-blender / cube blender. "
                "Blend at slow speed for 5 minutes (pre-blending).",
    },
    {
        "num": "4",
        "desc": "Add Magnesium Stearate. Blend for a further 5 minutes at slow speed.",
    },
    {
        "num": "5",
        "desc": "Collect blend uniformity samples from 3 positions (top, middle, bottom / left, center, right). "
                "Submit to QC; await result before filling.",
    },
    {
        "num": "6",
        "desc": "Discharge blended powder into sealed, labeled containers. "
                "Weigh containers (shell + blend) and record.",
    },
]

_FILLING_STEPS = [
    {
        "num": "1",
        "desc": "Verify that blend has been approved by QC for filling (blend uniformity result in BMR).",
    },
    {
        "num": "2",
        "desc": "Set up capsule filling machine: capsule size, feed hopper, tamping pins, and ejection settings.",
    },
    {
        "num": "3",
        "desc": "Charge capsule body and cap magazines. Verify correct capsule shell (size 0, hard gelatin) and lot number.",
    },
    {
        "num": "4",
        "desc": "Run a trial of 10 capsules. Weigh each: acceptable range = target fill weight ± 5%. "
                "Adjust tamping pins if outside range.",
    },
    {
        "num": "5",
        "desc": "Commence filling. Perform in-process weight checks every 30 minutes. "
                "Record all results in IPC sheets.",
    },
    {
        "num": "6",
        "desc": "QA to perform independent IPC checks at start, mid-batch, and end. "
                "Record on QA IPC sheet.",
    },
    {
        "num": "7",
        "desc": "Pass filled capsules through polishing machine. Collect in labeled containers.",
    },
    {
        "num": "8",
        "desc": "On batch completion, count total capsules and record. Complete yield reconciliation.",
    },
]

_BLISTER_STEPS = [
    {
        "num": "1",
        "desc": "Verify sorted capsules are approved and correctly labeled (BMR ref, AR No.).",
    },
    {
        "num": "2",
        "desc": "Load PVC/PVDC base film and aluminium lid foil. Check lot numbers and expiry of packaging materials.",
    },
    {
        "num": "3",
        "desc": "Set seal temperature (175–195°C), dwell time, and embossing pressure. "
                "Produce trial blister; QA checks seal integrity and legibility.",
    },
    {
        "num": "4",
        "desc": "Set printing / embossing: Batch No., Mfg Date, Expiry Date. "
                "Print sample and verify with QA before running.",
    },
    {
        "num": "5",
        "desc": "Commence blister packing. Perform in-process checks every 30 minutes: "
                "seal integrity, capsule fill, printing.",
    },
    {
        "num": "6",
        "desc": "Complete batch. Count total blisters and record. Transfer to secondary packing.",
    },
]

_SECONDARY_STEPS = [
    {
        "num": "1",
        "desc": "Verify blisters are approved; check Batch No., Mfg Date, Expiry Date on blisters match BMR.",
    },
    {
        "num": "2",
        "desc": "Set up coding machine for carton: Batch No., Mfg Date, Expiry Date, MRP. "
                "QA approves printed sample before running.",
    },
    {
        "num": "3",
        "desc": "Insert blister(s) + leaflet into carton. Fold and seal. Perform periodic checks.",
    },
    {
        "num": "4",
        "desc": "Pack cartons into shipper boxes (as per batch specification). Seal and label shipper boxes.",
    },
    {
        "num": "5",
        "desc": "Complete final reconciliation: Blisters in = Blisters packed + Rejected + Returned.",
    },
]

# ---------------------------------------------------------------------------
# Build sections
# ---------------------------------------------------------------------------

def _build_sections(template):
    from bmr.template_models import BMRTemplateSection

    s = []
    order = 0

    def sec(phase, section_type, title, config=None, page=1):
        nonlocal order
        order += 1
        return BMRTemplateSection(
            template=template,
            phase_name=phase,
            section_type=section_type,
            title=title,
            config=config or {},
            order=order,
            page_number=page,
            is_required=True,
            is_visible=True,
        )

    # ------------------------------------------------------------------ #
    # PHASE 1 — Material Dispensing
    # ------------------------------------------------------------------ #
    s.append(sec(
        "material_dispensing", "line_clearance",
        "Dispensing Area Line Clearance",
        config={
            "beginning_items": _DISPENSING_LINE_CLEARANCE_BEGINNING,
            "ending_items": _GENERIC_ENDING_ITEMS,
        },
        page=1,
    ))
    s.append(sec(
        "material_dispensing", "form",
        "Dispensing Record",
        config={
            "description": (
                "Record each raw material dispensed: "
                "Material Name, AR No., Required Qty (g/kg), "
                "Dispensed Qty (g/kg), Balance Used, Dispenser Initials, QA Initials."
            ),
        },
        page=1,
    ))

    # ------------------------------------------------------------------ #
    # PHASE 2 — Drying
    # ------------------------------------------------------------------ #
    s.append(sec(
        "drying", "line_clearance",
        "Drying Area Line Clearance",
        config={
            "beginning_items": _DRYING_BEGINNING,
            "ending_items": _DRYING_ENDING,
        },
        page=2,
    ))
    s.append(sec(
        "drying", "process_steps",
        "Drying Process Steps",
        config={
            "steps": _DRYING_STEPS,
            "has_timing": True,
            "timing_columns": ["Step No.", "Description", "Time On", "Time Off", "Temp (°C)", "Operator", "QA"],
            "equipment_list": [
                {"name": "Tray Dryer", "id": ""},
                {"name": "SS Trays (lined)", "id": ""},
                {"name": "40-Mesh Sieve", "id": ""},
                {"name": "Balance", "id": ""},
            ],
        },
        page=2,
    ))
    s.append(sec(
        "drying", "qa_report",
        "Post-Drying Quality Check (Loss on Drying)",
        config={
            "tests": [
                {"test": "Loss on Drying (LOD)", "spec": "NMT 13.0% w/w (Amoxicillin Trihydrate BP)"},
                {"test": "Appearance after drying", "spec": "White to pale yellow free-flowing powder"},
                {"test": "Sieve passage (40 mesh)", "spec": "Passes through 40-mesh — no lumps or agglomerates"},
            ],
            "has_comply": True,
            "next_stage": "Blending",
            "reject_note": "If LOD exceeds 13.0%, return to dryer and re-test before proceeding.",
        },
        page=2,
    ))
    s.append(sec(
        "drying", "yield_reconciliation",
        "Drying Yield Reconciliation",
        config={
            "rows": [
                {"key": "A", "label": "Weight of Amoxicillin Trihydrate before drying (kg)", "formula": ""},
                {"key": "B", "label": "Weight after drying (kg)", "formula": ""},
                {"key": "C", "label": "Loss on drying (kg)  [A − B]", "formula": "A-B"},
                {"key": "D", "label": "% Loss  [C ÷ A × 100]", "formula": "C/A*100"},
            ],
            "permissible": "See LOD specification above",
        },
        page=3,
    ))

    # ------------------------------------------------------------------ #
    # PHASE 3 — Blending
    # ------------------------------------------------------------------ #
    s.append(sec(
        "blending", "line_clearance",
        "Blending Area Line Clearance",
        config={
            "beginning_items": _BLENDING_BEGINNING,
            "ending_items": _BLENDING_ENDING,
        },
        page=4,
    ))
    s.append(sec(
        "blending", "process_steps",
        "Blending Process Steps",
        config={
            "steps": _BLENDING_STEPS,
            "has_timing": True,
            "equipment_list": [
                {"name": "V-Blender / Cube Blender", "id": ""},
                {"name": "60-Mesh Sieve (for Mg Stearate)", "id": ""},
                {"name": "SS Containers (sealed)", "id": ""},
            ],
        },
        page=4,
    ))
    s.append(sec(
        "blending", "qa_report",
        "Post-Blending In-Process Quality Report",
        config={
            "tests": [
                {"test": "Appearance", "spec": "White to off-white free-flowing powder"},
                {"test": "Blend Uniformity (RSD)", "spec": "NMT 5.0% (3 positions)"},
                {"test": "Moisture Content (Karl Fischer / LOD)", "spec": "NMT 13.0% w/w"},
                {"test": "Bulk Density", "spec": "As per approved standard"},
                {"test": "Identification — Amoxicillin (IR)", "spec": "Conforms to Reference Standard"},
            ],
            "has_comply": True,
            "next_stage": "Capsule Filling",
        },
        page=4,
    ))
    s.append(sec(
        "blending", "yield_reconciliation",
        "Blending Yield Reconciliation",
        config={
            "rows": [
                {"key": "A", "label": "Theoretical Blend Weight (kg)", "formula": ""},
                {"key": "B", "label": "Actual Blend Weight (kg) — net", "formula": ""},
                {"key": "C", "label": "Residue on blender walls / utensils (kg)", "formula": ""},
                {"key": "D", "label": "Blend sent to QC samples (g)", "formula": ""},
                {"key": "E", "label": "Total Accounted  [B + C + D in kg]", "formula": "B+C+D"},
                {"key": "F", "label": "Unaccounted (kg)  [A − E]", "formula": "A-E"},
                {"key": "G", "label": "% Yield  [B ÷ A × 100]", "formula": "B/A*100"},
            ],
            "permissible": "98.0% – 102.0%",
        },
        page=5,
    ))

    # ------------------------------------------------------------------ #
    # PHASE 4 — Capsule Filling
    # ------------------------------------------------------------------ #
    s.append(sec(
        "filling", "line_clearance",
        "Capsule Filling Area Line Clearance",
        config={
            "beginning_items": _FILLING_BEGINNING,
            "ending_items": _FILLING_ENDING,
        },
        page=6,
    ))
    s.append(sec(
        "filling", "equipment_setup",
        "Capsule Filling Machine Setup",
        config={
            "machine": "Automatic Hard Gelatin Capsule Filling Machine",
            "fields": [
                {"key": "machine_no", "label": "Machine No."},
                {"key": "capsule_size", "label": "Capsule Size"},
                {"key": "capsule_color", "label": "Capsule Color (Body / Cap)"},
                {"key": "target_fill_wt", "label": "Target Fill Weight (mg)"},
                {"key": "upper_limit", "label": "Upper Limit (mg)"},
                {"key": "lower_limit", "label": "Lower Limit (mg)"},
                {"key": "tamping_force", "label": "Tamping Force Setting"},
                {"key": "machine_speed", "label": "Machine Speed (caps/min)"},
                {"key": "setup_operator", "label": "Setup Operator"},
                {"key": "setup_qa", "label": "QA Check"},
            ],
            "filling_weight": {
                "nominal": 600,
                "upper_pct": 105,
                "lower_pct": 95,
                "uom": "mg",
            },
        },
        page=6,
    ))

    # Production IPC sheets
    for sheet_num in range(1, 4):
        s.append(sec(
            "filling", "ipc_table",
            f"Capsule Filling In-Process Control — Production Sheet {sheet_num}",
            config={
                "sheet_number": sheet_num,
                "ipc_type": "production",
                "fill_weight_spec": "Target fill weight ± 5%",
                "frequency": "Every 30 minutes",
            },
            page=7,
        ))

    # QA IPC sheets
    for sheet_num in range(1, 3):
        s.append(sec(
            "filling", "ipc_table",
            f"Capsule Filling In-Process Control — QA Sheet {sheet_num}",
            config={
                "sheet_number": sheet_num,
                "ipc_type": "qa",
                "fill_weight_spec": "Target fill weight ± 5%",
                "frequency": "Start / Mid / End of batch",
            },
            page=8,
        ))

    s.append(sec(
        "filling", "yield_reconciliation",
        "Capsule Filling Yield Reconciliation",
        config={
            "rows": [
                {"key": "A", "label": "Theoretical No. of Capsules", "formula": ""},
                {"key": "B", "label": "Capsule Shells Received (No.)", "formula": ""},
                {"key": "C", "label": "No. of Filled Capsules (Good)", "formula": ""},
                {"key": "D", "label": "No. of Rejected Capsules (IPC rejects)", "formula": ""},
                {"key": "E", "label": "Empty Capsule Shells Returned (No.)", "formula": ""},
                {"key": "F", "label": "Blend Residue in Machine (g)", "formula": ""},
                {"key": "G", "label": "% Yield  [C ÷ A × 100]", "formula": "C/A*100"},
            ],
            "permissible": "98.0% – 102.0%",
        },
        page=9,
    ))

    # ------------------------------------------------------------------ #
    # PHASE 5 — Sorting (visual inspection)
    # ------------------------------------------------------------------ #
    s.append(sec(
        "sorting", "line_clearance",
        "Sorting / Inspection Area Line Clearance",
        config={
            "beginning_items": [
                "Sorting area cleaned and cleared of previous product.",
                "Light boxes / inspection lamp clean and functional.",
                "Rejection containers labeled 'REJECTED CAPSULES'.",
                "Filled capsules verified (AR, BMR ref, count from filling).",
                "Sorting personnel gowned and trained.",
            ],
            "ending_items": _GENERIC_ENDING_ITEMS,
        },
        page=10,
    ))
    s.append(sec(
        "sorting", "form",
        "Sorting In-Process Control",
        config={
            "description": (
                "Record: Start time, No. capsules received, No. accepted (good), "
                "No. rejected (broken / deformed / under/over-filled / empty), "
                "Operator initials, QA initials, Remarks."
            ),
        },
        page=10,
    ))
    s.append(sec(
        "sorting", "yield_reconciliation",
        "Sorting Yield Reconciliation",
        config={
            "rows": [
                {"key": "A", "label": "No. of Capsules Received from Filling", "formula": ""},
                {"key": "B", "label": "No. of Accepted Capsules (Good)", "formula": ""},
                {"key": "C", "label": "No. Rejected — Broken / Deformed", "formula": ""},
                {"key": "D", "label": "No. Rejected — Under/Over-filled (IPC)", "formula": ""},
                {"key": "E", "label": "No. Rejected — Empty / Open", "formula": ""},
                {"key": "F", "label": "Total Rejected  [C + D + E]", "formula": "C+D+E"},
                {"key": "G", "label": "% Yield  [B ÷ A × 100]", "formula": "B/A*100"},
            ],
            "permissible": "NLT 97.0%",
        },
        page=10,
    ))

    # ------------------------------------------------------------------ #
    # PHASE 6 — Blister Packing
    # ------------------------------------------------------------------ #
    s.append(sec(
        "blister_packing", "line_clearance",
        "Blister Packing Area Line Clearance",
        config={
            "beginning_items": _BLISTER_BEGINNING,
            "ending_items": _BLISTER_ENDING,
        },
        page=11,
    ))
    s.append(sec(
        "blister_packing", "process_steps",
        "Blister Packing Process Steps",
        config={
            "steps": _BLISTER_STEPS,
            "has_timing": True,
            "equipment_list": [
                {"name": "Blister Packing Machine", "id": ""},
                {"name": "Coding / Embossing Unit", "id": ""},
                {"name": "Seal Integrity Tester", "id": ""},
            ],
        },
        page=11,
    ))

    # Production IPC sheets for blister
    for sheet_num in range(1, 3):
        s.append(sec(
            "blister_packing", "ipc_table",
            f"Blister Packing In-Process Control — Sheet {sheet_num}",
            config={
                "sheet_number": sheet_num,
                "ipc_type": "production",
                "frequency": "Every 30 minutes",
                "header_fields": [
                    {"key": "seal_temp", "label": "Seal Temp (°C)"},
                    {"key": "seal_time", "label": "Dwell Time (s)"},
                    {"key": "batch_no_check", "label": "Batch No. on Blister"},
                ],
            },
            page=12,
        ))

    s.append(sec(
        "blister_packing", "yield_reconciliation",
        "Blister Packing Yield Reconciliation",
        config={
            "rows": [
                {"key": "A", "label": "No. of Sorted Capsules Received", "formula": ""},
                {"key": "B", "label": "No. of Blisters Packed (Good)", "formula": ""},
                {"key": "C", "label": "No. of Capsules per Blister", "formula": ""},
                {"key": "D", "label": "Total Capsules Used in Good Blisters  [B × C]", "formula": "B*C"},
                {"key": "E", "label": "Capsules Rejected during Blister Packing", "formula": ""},
                {"key": "F", "label": "Total Foil / Film Used (metres or kg)", "formula": ""},
                {"key": "G", "label": "% Yield  [D ÷ A × 100]", "formula": "D/A*100"},
            ],
            "permissible": "98.0% – 102.0%",
        },
        page=13,
    ))

    # ------------------------------------------------------------------ #
    # PHASE 7 — Secondary Packaging
    # ------------------------------------------------------------------ #
    s.append(sec(
        "secondary_packaging", "line_clearance",
        "Secondary Packing Area Line Clearance",
        config={
            "beginning_items": [
                "Previous product / batch completely cleared from packing area.",
                "Correct cartons, leaflets, labels and shipper boxes available.",
                "Batch No., Mfg Date, Expiry Date verified on all packaging materials.",
                "Coding machine cleaned and programmed — sample printed and approved by QA.",
                "Packing area temperature and humidity recorded.",
                "BMR and packing records available at packing station.",
            ],
            "ending_items": _GENERIC_ENDING_ITEMS,
        },
        page=14,
    ))
    s.append(sec(
        "secondary_packaging", "process_steps",
        "Secondary Packing Process Steps",
        config={
            "steps": _SECONDARY_STEPS,
            "has_timing": True,
        },
        page=14,
    ))
    s.append(sec(
        "secondary_packaging", "coding_control",
        "Coding Control and Reconciliation",
        config={
            "coding_fields": [
                {"key": "batch_no", "label": "Batch No. coded"},
                {"key": "mfg_date", "label": "Manufacturing Date"},
                {"key": "exp_date", "label": "Expiry Date"},
                {"key": "price", "label": "MRP / Price (if applicable)"},
                {"key": "coding_operator", "label": "Coding Operator Initials"},
                {"key": "qa_check", "label": "QA Verification Initials"},
            ],
            "packer_count": 6,
            "reconcile_fields": [
                {"key": "cartons_received", "label": "Cartons Received"},
                {"key": "cartons_used", "label": "Cartons Used (Good)"},
                {"key": "cartons_rejected", "label": "Cartons Rejected (damaged / misprinted)"},
                {"key": "cartons_returned", "label": "Cartons Returned to Store"},
                {"key": "cartons_balance", "label": "Balance (should be 0)"},
                {"key": "leaflets_received", "label": "Leaflets Received"},
                {"key": "leaflets_used", "label": "Leaflets Used"},
                {"key": "leaflets_returned", "label": "Leaflets Returned"},
            ],
        },
        page=15,
    ))

    for sheet_num in range(1, 3):
        s.append(sec(
            "secondary_packaging", "ipc_table",
            f"Secondary Packing IPC Check — Sheet {sheet_num}",
            config={
                "sheet_number": sheet_num,
                "ipc_type": "production",
                "frequency": "Every 30 minutes",
            },
            page=15,
        ))

    s.append(sec(
        "secondary_packaging", "yield_reconciliation",
        "Secondary Packing Yield Reconciliation",
        config={
            "rows": [
                {"key": "A", "label": "No. of Blisters Received from Blister Packing", "formula": ""},
                {"key": "B", "label": "No. of Blisters Packed (in cartons)", "formula": ""},
                {"key": "C", "label": "No. of Blisters Rejected during Packing", "formula": ""},
                {"key": "D", "label": "No. of Blisters Retained as Samples", "formula": ""},
                {"key": "E", "label": "No. of Blisters Unaccounted / Damaged", "formula": ""},
                {"key": "F", "label": "Total Accounted  [B + C + D + E]", "formula": "B+C+D+E"},
                {"key": "G", "label": "% Yield  [B ÷ A × 100]", "formula": "B/A*100"},
            ],
            "permissible": "98.0% – 102.0%",
        },
        page=16,
    ))

    return s
