"""
Management command to seed the MCG Ointment BMR dynamic template.

Run:
    python manage.py seed_bmr_ointment_template
    python manage.py seed_bmr_ointment_template --overwrite  (delete existing and re-create)

Sections are keyed by (product_type='ointment') on BMRTemplate.
"""

from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Seed dynamic BMR template sections for MCG Ointment (product_type='ointment')"

    def add_arguments(self, parser):
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Delete the existing ointment template and recreate from scratch.",
        )

    def handle(self, *args, **options):
        from bmr.models import BMRTemplate
        from bmr.template_models import BMRTemplateSection

        overwrite = options["overwrite"]

        with transaction.atomic():
            existing = BMRTemplate.objects.filter(product_type="ointment").first()
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
                name="MCG Ointment BMR Template",
                product_type="ointment",
                description="Dynamic BMR template for MCG Ointment (Miconazole + Clobetasol + Gentamycin cream). "
                            "Covers material dispensing, mixing, tube filling, and secondary packaging.",
                is_active=False,
            )
            self.stdout.write(self.style.SUCCESS(f"Created template: {template.name}  (pk={template.pk})"))

            sections = _build_sections(template)
            BMRTemplateSection.objects.bulk_create(sections)
            self.stdout.write(self.style.SUCCESS(f"Created {len(sections)} sections across all phases."))

        self.stdout.write(self.style.SUCCESS("Done — MCG Ointment template seeded successfully."))


# ---------------------------------------------------------------------------
# Section definitions
# ---------------------------------------------------------------------------

_LINE_CLEARANCE_BEGINNING = [
    "Area cleaning is done as per SOP.",
    "Ensure absence of previous product/batch remnants.",
    "Verify BMR availability and all materials labeled / identified.",
    "Gowning procedure is followed.",
    "Dispensing area, balances and tools are clean and ready.",
    "Clean scoops, containers and poly bags available as per SOP.",
    "Manometer reading of RLAF is within the required limit.",
    "Balance calibration carried out before dispensing.",
    "Verify release status and retest validity of each raw material.",
    "Environmental conditions met: Temp NMT 28°C, RH 40–65%.",
    "RLAF started 15 minutes before dispensing activities.",
]

_LINE_CLEARANCE_ENDING_GENERIC = [
    "Area/equipment cleaned as per SOP after operation.",
    "All materials labeled, sealed and moved to correct storage.",
    "Waste disposed as per SOP.",
    "Logbooks / BMR entries completed.",
    "Equipment status labels updated.",
    "Supervisor / QA review done before area release.",
]

_LINE_CLEARANCE_ENDING_MIXING = [
    "Planetary mixer and all attachments cleaned as per SOP.",
    "No product residue visible on equipment or bench surfaces.",
    "Batch identified and transferred to tube-filling room.",
    "Yield reconciliation completed in BMR.",
    "Logbooks and BMR entries signed and dated.",
    "QA reviewed and released area for next batch.",
]

_LINE_CLEARANCE_ENDING_TUBE_FILLING = [
    "Tube filling machine cleaned as per SOP after end of batch.",
    "All filled tubes counted and transferred to secondary packing.",
    "Empty-tube, carton, and leaflet reconciliation recorded.",
    "Machine maintenance log updated if applicable.",
    "Logbooks and BMR entries completed and signed.",
    "QA reviewed and released area for next batch.",
]

_LINE_CLEARANCE_ENDING_SECONDARY = [
    "All packed cartons labeled and transferred to FGS.",
    "Unused cartons, leaflets and labels reconciled and returned.",
    "Secondary packing area cleaned as per SOP.",
    "Logbooks and BMR entries completed and signed.",
    "Batch release sample submitted to QC if required.",
    "QA reviewed and released area for next batch.",
]

_MIXING_PROCESS_STEPS = [
    {
        "num": "1",
        "desc": "Verify all raw materials have been dispensed, identified and weighed correctly per BMR.",
    },
    {
        "num": "2",
        "desc": "Check that the planetary mixer, blades and utensils are clean, dry and labeled 'CLEANED'.",
    },
    {
        "num": "3",
        "desc": "Add Cetostearyl Alcohol (14.04 kg) and Cetomacrogol 1000 (6 kg) to the Planetary Mixer. "
                "Heat oil phase to 70°C with continuous slow-speed mixing.",
    },
    {
        "num": "4",
        "desc": "In a separate vessel heat Purified Water to 80°C. "
                "Add Chlorocresol (600 g) to water phase and stir until dissolved.",
    },
    {
        "num": "5",
        "desc": "Add Miconazole Nitrate (2.40 kg) and Clobetasol Propionate (60 g) to the oil phase "
                "while maintaining 70°C. Mix at slow speed for 5 minutes.",
    },
    {
        "num": "6",
        "desc": "Add Gentamycin Sulphate (120 g) to oil phase. Mix at slow speed for 5 minutes.",
    },
    {
        "num": "7",
        "desc": "Slowly pour hot water phase (80°C) into oil phase with continuous mixing at medium speed. "
                "Emulsify for 30 minutes.",
    },
    {
        "num": "8",
        "desc": "Allow product to cool to 40°C with continuous slow-speed mixing.",
    },
    {
        "num": "9",
        "desc": "Add Sodium Acid Phosphate (140 g) dissolved in a small quantity of Purified Water. Mix for 10 minutes.",
    },
    {
        "num": "10",
        "desc": "Note final batch temperature when mixing is complete. Record time on / time off for each step.",
    },
]

_MIXING_QA_TESTS = [
    {"test": "Appearance", "spec": "White smooth homogeneous cream, free from lumps"},
    {"test": "Colour", "spec": "White to off-white"},
    {"test": "Odour", "spec": "Characteristic"},
    {"test": "pH (1% w/v in water)", "spec": "5.5 – 7.0"},
    {"test": "Viscosity", "spec": "As per approved standard (NLT 80 000 cP)"},
    {"test": "Identification – Miconazole", "spec": "Positive"},
    {"test": "Identification – Clobetasol", "spec": "Positive"},
]

_TUBE_FILLING_PROCESS_STEPS = [
    {
        "num": "1",
        "desc": "Verify that the correct batch of cream is presented and identified with correct label.",
    },
    {
        "num": "2",
        "desc": "Set up tube filling machine: nozzle size, fill volume (15 g or 30 g as per batch size), "
                "seal temperature and sealing pressure.",
    },
    {
        "num": "3",
        "desc": "Charge tubes: ensure correct tube (printed or blank) as specified in the batch. "
                "Verify tube lot number and expiry date against BMR.",
    },
    {
        "num": "4",
        "desc": "Perform initial weight check: fill 10 tubes, weigh individually. "
                "Acceptable range: label claim ± 5%. Adjust machine if out of range.",
    },
    {
        "num": "5",
        "desc": "Commence filling. Perform in-process weight checks every 30 minutes. "
                "Record all results in IPC table.",
    },
    {
        "num": "6",
        "desc": "QA to perform independent IPC checks at start, mid-batch and end-batch. "
                "Record results in QA IPC sheet.",
    },
    {
        "num": "7",
        "desc": "On batch completion, obtain final tube count and record. "
                "Complete yield reconciliation.",
    },
]

_TUBE_FILLING_IPC_PRODUCTION_COLUMNS = [
    "Time", "Tube No.", "Gross Weight (g)", "Empty Tube (g)", "Net Weight (g)", "Operator Initials",
]

_TUBE_FILLING_IPC_QA_COLUMNS = [
    "Time", "Tube No.", "Gross Weight (g)", "Empty Tube (g)", "Net Weight (g)", "QA Initials", "Status (Pass/Fail)",
]

_SECONDARY_PACKING_PROCESS_STEPS = [
    {
        "num": "1",
        "desc": "Verify tube labels, cartons and leaflets are correct for this batch. "
                "Check Batch No., Mfg Date, Expiry Date against BMR.",
    },
    {
        "num": "2",
        "desc": "Set up coding machine: Batch No., Mfg Date, Expiry Date. "
                "Print sample and verify with QA before commencing.",
    },
    {
        "num": "3",
        "desc": "Commence packing: insert tube + leaflet into carton, fold and seal. "
                "Periodic checks every 30 minutes.",
    },
    {
        "num": "4",
        "desc": "Assembled cartons packed into shipper boxes (12 or 24 per box as specified). "
                "Seal and label each shipper box.",
    },
    {
        "num": "5",
        "desc": "Perform final count reconciliation: Tubes in = Tubes packed + Rejects + Returns.",
    },
]


def _build_sections(template):
    """Return a list of unsaved BMRTemplateSection objects for the given template."""
    from bmr.template_models import BMRTemplateSection

    s = []  # accumulator
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
            "beginning_items": _LINE_CLEARANCE_BEGINNING,
            "ending_items": _LINE_CLEARANCE_ENDING_GENERIC,
        },
        page=1,
    ))
    s.append(sec(
        "material_dispensing", "form",
        "Dispensing Record",
        config={
            "description": (
                "Record each raw material dispensed: Material Name, AR No., "
                "Required Qty (kg/g), Dispensed Qty (kg/g), Balance Used, "
                "Dispenser Initials, QA Initials."
            ),
        },
        page=1,
    ))

    # ------------------------------------------------------------------ #
    # PHASE 2 — Mixing
    # ------------------------------------------------------------------ #
    s.append(sec(
        "mixing", "line_clearance",
        "Mixing Room Line Clearance",
        config={
            "beginning_items": [
                "Mixing room cleaned as per SOP — no remnants of previous product.",
                "Planetary mixer, blades and attachments cleaned and labeled 'CLEANED'.",
                "All vessels, spatulas, thermometers and utensils clean and ready.",
                "Ensure air flow / HVAC conditions are acceptable.",
                "BMR and weighing records available and verified.",
                "All dispensed materials present and quantity is as per BMR.",
                "Temperature and humidity recorded at start of operation.",
            ],
            "ending_items": _LINE_CLEARANCE_ENDING_MIXING,
        },
        page=2,
    ))
    s.append(sec(
        "mixing", "process_steps",
        "Mixing Process Steps",
        config={
            "steps": _MIXING_PROCESS_STEPS,
            "has_timing": True,
            "timing_columns": ["Step No.", "Description", "Time On", "Time Off", "Operator", "QA"],
        },
        page=2,
    ))
    s.append(sec(
        "mixing", "qa_report",
        "Post-Mixing In-Process Quality Report",
        config={
            "tests": _MIXING_QA_TESTS,
            "has_comply": True,
            "next_stage": "Tube Filling",
            "sample_size": "Approx. 50 g from top, middle and bottom of batch",
        },
        page=2,
    ))
    s.append(sec(
        "mixing", "yield_reconciliation",
        "Mixing Yield Reconciliation",
        config={
            "rows": [
                {"key": "A", "label": "Theoretical Yield (kg)", "formula": ""},
                {"key": "B", "label": "Weight of empty mixing vessel (kg)", "formula": ""},
                {"key": "C", "label": "Weight of mixing vessel + product (kg)", "formula": ""},
                {"key": "D", "label": "Actual Yield \u2014 batch (kg)  [C \u2212 B]", "formula": "C-B"},
                {"key": "E", "label": "Product transferred to tube filling (kg)", "formula": ""},
                {"key": "F", "label": "Residue / wastage (kg)  [D \u2212 E]", "formula": "D-E"},
                {"key": "G", "label": "% Yield  [D \u00f7 A \u00d7 100]", "formula": "D/A*100"},
            ],
            "permissible": "98.0% \u2013 102.0%",
        },
        page=3,
    ))

    # ------------------------------------------------------------------ #
    # PHASE 3 — Tube Filling
    # ------------------------------------------------------------------ #
    s.append(sec(
        "tube_filling", "line_clearance",
        "Tube Filling Area Line Clearance",
        config={
            "beginning_items": [
                "Tube filling area cleaned per SOP — no previous product remnants.",
                "Tube filling machine cleaned and status label reads 'CLEANED'.",
                "Correct tubes, nozzles, and accessories available and identified.",
                "BMR, batch cream and IPC records available at filling station.",
                "Temperature and humidity within specification (NMT 28°C, RH 40–65%).",
                "Batch cream identified and status confirmed 'APPROVED FOR FILLING'.",
            ],
            "ending_items": _LINE_CLEARANCE_ENDING_TUBE_FILLING,
        },
        page=4,
    ))
    s.append(sec(
        "tube_filling", "equipment_setup",
        "Tube Filling Machine Setup",
        config={
            "machine": "Automatic Tube Filling & Sealing Machine",
            "fields": [
                {"key": "nozzle_size", "label": "Nozzle Size (mm)"},
                {"key": "fill_volume_set", "label": "Fill Volume Set (g)"},
                {"key": "seal_temp", "label": "Seal Temperature (°C)"},
                {"key": "seal_pressure", "label": "Seal Pressure (bar)"},
                {"key": "line_speed", "label": "Line Speed (tubes/min)"},
                {"key": "setup_operator", "label": "Setup Operator"},
                {"key": "setup_qa", "label": "QA Check"},
                {"key": "setup_time", "label": "Setup Time"},
            ],
            "initial_weight_check": {
                "sample_size": 10,
                "acceptable_range_pct": 5,
                "columns": ["Tube No.", "Gross Wt (g)", "Empty Tube (g)", "Net Wt (g)", "Pass/Fail"],
            },
        },
        page=4,
    ))

    # Production IPC sheets (3 sheets covering start, mid, end)
    for sheet_num in range(1, 4):
        s.append(sec(
            "tube_filling", "ipc_table",
            f"Tube Filling In-Process Control — Production Sheet {sheet_num}",
            config={
                "sheet_number": sheet_num,
                "ipc_type": "production",
                "columns": _TUBE_FILLING_IPC_PRODUCTION_COLUMNS,
                "rows_per_sheet": 10,
                "fill_weight_spec": "Label claim ± 5%",
                "frequency": "Every 30 minutes",
            },
            page=5,
        ))

    # QA IPC sheets (2 independent QA checks)
    for sheet_num in range(1, 3):
        s.append(sec(
            "tube_filling", "ipc_table",
            f"Tube Filling In-Process Control — QA Sheet {sheet_num}",
            config={
                "sheet_number": sheet_num,
                "ipc_type": "qa",
                "columns": _TUBE_FILLING_IPC_QA_COLUMNS,
                "rows_per_sheet": 5,
                "fill_weight_spec": "Label claim ± 5%",
                "frequency": "Start / Mid / End of batch",
            },
            page=6,
        ))

    s.append(sec(
        "tube_filling", "yield_reconciliation",
        "Tube Filling Yield Reconciliation",
        config={
            "rows": [
                {"key": "A", "label": "Theoretical No. of Tubes", "formula": ""},
                {"key": "B", "label": "No. of Tubes Received from Mixing", "formula": ""},
                {"key": "C", "label": "No. of Filled Tubes (Good)", "formula": ""},
                {"key": "D", "label": "No. of Rejected Tubes", "formula": ""},
                {"key": "E", "label": "Cream Residue in Machine (kg)", "formula": ""},
                {"key": "F", "label": "Total Accounted  [C + D + E in tube equivalent]", "formula": "C+D+E"},
                {"key": "G", "label": "% Yield  [C \u00f7 A \u00d7 100]", "formula": "C/A*100"},
            ],
            "permissible": "98.0% \u2013 102.0%",
        },
        page=7,
    ))

    # ------------------------------------------------------------------ #
    # PHASE 4 — Secondary Packaging
    # ------------------------------------------------------------------ #
    s.append(sec(
        "secondary_packaging", "line_clearance",
        "Packing Area Line Clearance",
        config={
            "beginning_items": [
                "Previous product / batch completely cleared from packing area.",
                "Correct cartons, leaflets, labels and shipper boxes available.",
                "Batch No., Mfg Date, Expiry Date verified on all packaging materials.",
                "Coding machine cleaned and programmed — sample printed and approved by QA.",
                "Packing area temperature and humidity recorded.",
                "BMR and packing records available at packing station.",
            ],
            "ending_items": _LINE_CLEARANCE_ENDING_SECONDARY,
        },
        page=8,
    ))
    s.append(sec(
        "secondary_packaging", "process_steps",
        "Secondary Packing Process Steps",
        config={
            "steps": _SECONDARY_PACKING_PROCESS_STEPS,
            "has_timing": True,
            "timing_columns": ["Step", "Description", "Time", "Done By", "QA Check"],
        },
        page=8,
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
                {"key": "coding_operator", "label": "Coding Operator"},
                {"key": "qa_check", "label": "QA Verification Initials"},
            ],
            "packer_count": 4,
            "reconcile_fields": [
                {"label": "Cartons Received", "key": "cartons_received"},
                {"label": "Cartons Used (Good)", "key": "cartons_used"},
                {"label": "Cartons Rejected (damaged / misprinted)", "key": "cartons_rejected"},
                {"label": "Cartons Returned to Store", "key": "cartons_returned"},
                {"label": "Balance (should be 0)", "key": "cartons_balance"},
                {"label": "Leaflets Received", "key": "leaflets_received"},
                {"label": "Leaflets Used", "key": "leaflets_used"},
                {"label": "Leaflets Returned", "key": "leaflets_returned"},
            ],
        },
        page=9,
    ))

    # 3 secondary IPC (appearance / label / packed unit checks)
    for sheet_num in range(1, 4):
        s.append(sec(
            "secondary_packaging", "ipc_table",
            f"Secondary Packing IPC Check — Sheet {sheet_num}",
            config={
                "sheet_number": sheet_num,
                "ipc_type": "production",
                "columns": [
                    "Time", "Sample No.", "Label Check", "Carton Code Check",
                    "Leaflet Present", "Packer Initials", "QA Initials", "Status",
                ],
                "rows_per_sheet": 10,
                "frequency": "Every 30 minutes",
                "checks": [
                    "Correct label / carton",
                    "Batch No., Mfg/Exp Date legible and correct",
                    "No smearing / misprint on code",
                    "Leaflet present and correctly placed",
                    "Carton properly sealed",
                ],
            },
            page=9,
        ))

    s.append(sec(
        "secondary_packaging", "yield_reconciliation",
        "Secondary Packing Yield Reconciliation",
        config={
            "rows": [
                {"key": "A", "label": "No. of Filled Tubes Received from Tube Filling", "formula": ""},
                {"key": "B", "label": "No. of Tubes Packed (in cartons)", "formula": ""},
                {"key": "C", "label": "No. of Tubes Rejected during Packing", "formula": ""},
                {"key": "D", "label": "No. of Tubes Retained as Samples", "formula": ""},
                {"key": "E", "label": "No. of Tubes Unaccounted / Breakage", "formula": ""},
                {"key": "F", "label": "Total Accounted  [B + C + D + E]", "formula": "B+C+D+E"},
                {"key": "G", "label": "% Yield  [B \u00f7 A \u00d7 100]", "formula": "B/A*100"},
            ],
            "permissible": "98.0% \u2013 102.0%",
        },
        page=10,
    ))

    return s
