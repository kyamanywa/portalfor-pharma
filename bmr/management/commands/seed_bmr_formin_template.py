"""
Management command to seed the Formin Coated Tablet BMR dynamic template.

Product: Formin (Metformin Hydrochloride BP 500mg Film-Coated Tablets)
Type   : tablet (standard tablet workflow + coating + blister packing)

Run:
    python manage.py seed_bmr_formin_template
    python manage.py seed_bmr_formin_template --overwrite
"""

from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Seed dynamic BMR template for Formin (Metformin HCl 500mg Coated Tablets, product_type='tablet')"

    def add_arguments(self, parser):
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Delete existing tablet template and recreate from scratch.",
        )

    def handle(self, *args, **options):
        from bmr.models import BMRTemplate
        from bmr.template_models import BMRTemplateSection

        overwrite = options["overwrite"]

        with transaction.atomic():
            existing = BMRTemplate.objects.filter(product_type="tablet").first()
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
                name="Formin Coated Tablet BMR Template",
                product_type="tablet",
                description=(
                    "Dynamic BMR template for Formin — "
                    "Metformin Hydrochloride Tablets BP 500mg Film-Coated. "
                    "Batch Size: 500,000 Tablets. MFR No.: KPI/MFR/014/00. BMR Revision: 03. "
                    "Covers material dispensing, granulation (2 lots), blending/lubrication, "
                    "tablet compression, post-compression QC, sorting, film coating (4 lots), "
                    "blister packing and secondary packaging."
                ),
                is_active=False,
            )
            self.stdout.write(self.style.SUCCESS(f"Created template: {template.name}  (pk={template.pk})"))

            sections = _build_sections(template)
            BMRTemplateSection.objects.bulk_create(sections)
            self.stdout.write(self.style.SUCCESS(f"Created {len(sections)} sections across all phases."))

        self.stdout.write(self.style.SUCCESS("Done — Formin Coated Tablet template seeded successfully."))


# ---------------------------------------------------------------------------
# Reusable line-clearance and ending lists
# ---------------------------------------------------------------------------

_GENERIC_BEGIN = [
    "Area cleaned and cleared of all remnants of previous batch / previous product.",
    "Equipment cleaning records verified — 'CLEANED' labels in place.",
    "BMR and all relevant SOPs available and accessible in the area.",
    "All personnel gowned as per SOP.",
    "Environmental conditions met: Temperature NMT 28°C, RH 40–65%.",
    "Status board displayed: Product Name, Batch No., Batch Size, Mfg Date, Exp Date.",
]

_DISPENSING_BEGIN = [
    "RLAF booth started minimum 15 minutes before dispensing; manometer reading within required limits.",
    "Balance calibration carried out before starting dispensing (Balance IDs: B-46, B-28, B-59).",
    "All raw materials verified by AR number; release status and retest validity period confirmed.",
    "Clean scoops, containers and poly bags available for dispensing as per SOP.",
    "No remnants of previous product in dispensing booth or RLAF area.",
    "Environmental conditions: Temperature NMT 28°C, Relative Humidity 40–65%.",
    "Dispensing performed in presence of: 1 Store, 1 QA, 1 Production representative.",
]

_GENERIC_END = [
    "Product / in-process material transferred to next stage in sealed, labeled containers.",
    "Area and equipment cleaned and sanitised as per SOP.",
    "BMR entries completed and signed.",
    "Equipment status labels updated.",
    "Waste disposed of as per SOP.",
    "QA reviewed and counter-signed relevant sections.",
]

_GRANULATION_BEGIN = [
    "Area cleaned as per SOP; no remnants of previous product in granulation area.",
    "Vibro-sifter, Paste Kettle, RMG, FBD, Comminuting Mill cleaned and 'CLEANED' labeled.",
    "Vibrosifter sieves, Comminuting Mill screen, FBD bags, scoops cleaned and confirmed.",
    "FBD gasket integrity / bowl sieve / Dutch mesh / distribution plate checked.",
    "Balance calibration and verification records updated.",
    "Environmental conditions: Temperature NMT 28°C, RH 40–65%.",
    "Status board displayed with Product Name, Batch No., Batch Size, Mfg. Date, Exp. Date.",
]

_COMPRESSION_BEGIN = [
    "Area cleaned as per SOP; previous product containers, materials and labels removed.",
    "Compression machine cleaned and 'CLEANED' labeled.",
    "Correct D-tooling installed: 12.5 mm round shallow concave plain punches (Trade and UG).",
    "Initial punch/die inspection record completed — all stations checked.",
    "IPC balance calibrated; hardness tester, thickness gauge and disintegration apparatus ready.",
    "Blended granules verified against BMR reference and AR number.",
    "Environmental conditions: Temperature NMT 28°C, RH 40–65%.",
]

_COATING_BEGIN = [
    "Area cleaned as per SOP; previous product containers, materials and labels removed.",
    "Coating pan, spray gun assembly, silicon tubes, hot air blower pipes and exhaust pipes cleaned.",
    "Balance calibration and verification records updated.",
    "Sorted tablets received from Sorting/SMFPQ with transfer record and count verified.",
    "Coating dispersion ingredients (HPMC, PEG 6000, Propylene Glycol, Methylene Chloride, IPA, TiO₂, Talc) verified.",
    "Environmental conditions: Temperature NMT 28°C, RH 40–65%.",
]

_BLISTER_BEGIN = [
    "Area cleaned as per SOP; all previous product material removed from packaging line.",
    "Blister machine cleaned and 'CLEANED' labeled.",
    "PVC clear film 206×0.25mm and printed aluminium foil 203×0.25mm verified (AR No., expiry).",
    "Seal and forming temperature settings confirmed as per BMR.",
    "Trial blister produced; seal integrity (leak test) approved by QA before run.",
    "Coding checked: Batch No., Mfg Date, Expiry Date legible, correct — QA approved coded sample.",
    "Environmental conditions: Temperature NMT 28°C, RH 40–65%.",
]

# ---------------------------------------------------------------------------
# Process step lists
# ---------------------------------------------------------------------------

_DISPENSING_STEPS = [
    # No process_steps section needed for dispensing — covered by LC + form
]

_GRANULATION_STEPS = [
    {"num": "A-1", "desc": "DRY MIXING (per lot): Sift 125.00 kg Metformin HCl BP and 1.765 kg Microcrystalline Cellulose BP "
                          "through mesh #20 fitted to a vibrator sifter into a double polythene-lined drum."},
    {"num": "A-2", "desc": "Transfer sifted materials into the Rapid Mixer Granulator (RMG). Mix for 10 minutes at SLOW speed, "
                          "then at FAST speed for 5 minutes. Record RMG number, impeller RPM and chopper RPM."},
    {"num": "B-3", "desc": "BINDER PREPARATION: Sift 6.62 kg Povidone K-30 BP through sieve #40 into a double polythene-lined bag."},
    {"num": "B-4", "desc": "Make a slurry of sifted Povidone K-30 with 3.25 litres of purified water at room temperature in a stainless-steel vessel."},
    {"num": "B-5", "desc": "Boil 17.5 litres of purified water in a separate stainless-steel vessel."},
    {"num": "B-6", "desc": "Add the hot boiling water to the slurry (step B-4) while vigorously stirring to form a smooth uniform paste (binder solution)."},
    {"num": "B-7", "desc": "WET MIXING: Add the binder solution to the dry blend in the RMG. Mix at SLOW speed for 10 minutes then FAST speed for 10 minutes. "
                          "Add additional purified water with continuous mixing if required to achieve correct granulation end-point."},
    {"num": "B-8", "desc": "Unload the wet mass into the Fluid Bed Dryer (FBD) bowl. Record weight."},
    {"num": "C-9", "desc": "FIRST DRYING: Dry granules in FBD at inlet temperature 60°C for 45 minutes. "
                           "Record observed inlet temp, drying temp, outlet temp, start and complete times."},
    {"num": "C-10", "desc": "Remove granules from FBD and turn around with a stainless-steel scoop. "
                            "Mill granules in Comminuting Mill fitted with sieve size 10."},
    {"num": "C-11", "desc": "SECOND DRYING: Return milled granules to FBD. Re-dry at inlet temperature 60°C for 45 minutes. "
                            "Record inlet, drying and outlet temperatures."},
    {"num": "C-12", "desc": "FINAL MILLING: Cool granules to room temperature. Mill with Milling machine fitted with sieve No. 2.5. "
                            "Check LOD on IR Balance at 105°C (Limit: 1–4% w/w). Record LOD result."},
    {"num": "D-13", "desc": "Weigh dried milled granules. Record drum numbers, gross weight, tare weight and net weight for each drum. "
                            "Calculate and record total and theoretical weight."},
]

_BLENDING_STEPS = [
    {"num": "1", "desc": "Verify dried milled granules: correct BMR AR number, LOD within 1.0–4.0%, match BMR reference."},
    {"num": "2", "desc": "Sift and transfer into Double Cone Blender using Vibrosifter with the following sieves:\n"
                         "   a. Dried Granules — sift through mesh #12.\n"
                         "   b. 5.29 kg Croscarmellose Sodium BP — sift through mesh #40.\n"
                         "   c. 1.176 kg Purified Talc BP — sift through mesh #40.\n"
                         "   (Keep 1.764 kg Magnesium Stearate BP aside for lubrication step — sift #40 separately.)"},
    {"num": "3", "desc": "Add any recoveries from previous steps if applicable. Record batch numbers and quantities."},
    {"num": "4", "desc": "Transfer dried granules + Croscarmellose Sodium + Purified Talc into Double Cone Blender. "
                         "Mix for 15 minutes. Record start time, completion time and time taken."},
    {"num": "5", "desc": "Add Magnesium Stearate BP (1.764 kg, sifted #40) to the blend. Mix for 5 minutes. "
                         "Record start time, completion time and time taken."},
    {"num": "6", "desc": "Unload lubricated blend into double polybag-lined containers. "
                         "Record total number of containers, individual and total net weight. Apply product detail labels."},
    {"num": "7", "desc": "Take blend samples from Top, Middle and Bottom for LOD and homogeneity check. "
                         "Send to QA lab with this record. Spec: LOD 1.0–4.0% by IR moisture balance."},
]

_COMPRESSION_STEPS = [
    {"num": "1", "desc": "Verify lubricated blend is approved for compression. Check QC blend release in BMR. "
                         "Confirm correct AR nos. and BMR reference on blend containers."},
    {"num": "2", "desc": "MACHINE SETUP — D-Tooling; Punch size 12.5 mm round shallow concave plain on both sides. "
                         "Check initial dies and punches (all stations, both upper and lower). Record in station table."},
    {"num": "3", "desc": "Charge blend into hopper. Run feeder for 1 minute. Run machine at low speed. "
                         "Collect tablets of first 3 rounds and discard as non-recoverable residues."},
    {"num": "4", "desc": "Set tablet weight: check 20 tablets as a group (×3 sets). Calculate average weight. "
                         "Target nominal weight: 550.0 mg. Adjust weight dossier (anti-clockwise = increase, clockwise = decrease)."},
    {"num": "5", "desc": "Check initial individual weights of all punch stations (LHS and RHS). Record in station weight table."},
    {"num": "6", "desc": "Check initial hardness (NLT 3 kg/cm²), thickness (5.00 ± 0.3 mm) and diameter (12.5 ± 0.1 mm) of all station tablets."},
    {"num": "7", "desc": "Check initial disintegration time (NMT 15 min) and friability (NMT 1.0%). Visually inspect for defects."},
    {"num": "8", "desc": "Run batch at approved speed. Perform IPC every 60 minutes: "
                         "appearance (all stations), group weight (20 tabs/side), individual weight (all stations/side), "
                         "disintegration (6 tabs/side), hardness (all stations), thickness (all stations), friability (20 tabs/side)."},
    {"num": "9", "desc": "QA to perform independent IPC checks. Record in QA IPC sheets."},
    {"num": "10", "desc": "Complete batch compression. Record number of tablets, total weight and batch transfer to SMFPQ store."},
]

_SORTING_STEPS = [
    {"num": "1", "desc": "Receive compressed tablets with correct BMR reference."},
    {"num": "2", "desc": "Inspect tablets visually on light box — reject: broken, capped, chipped, "
                         "mottled, double-impressed or over/under-weight."},
    {"num": "3", "desc": "Record number accepted and rejected by defect category."},
    {"num": "4", "desc": "Transfer good tablets to coating room in clean, sealed containers with labels."},
]

_COATING_STEPS = [
    {"num": "1", "desc": "COATING DISPERSION PREPARATION (4 lots; perform the following for each lot):\n"
                         "   1. Place 16.50 kg Methylene Chloride in a clean S.S. mixing vessel.\n"
                         "   2. In a separate vessel: dissolve 75.00 g PEG 6000 in 3.0 kg Methylene Chloride, then add to Step 1.\n"
                         "   3. Add 66.25 g Propylene Glycol to Step 1 while stirring continuously.\n"
                         "   4. In a separate vessel: dissolve 500.00 g HPMC in 4.50 kg Isopropanol Alcohol to form a smooth slurry, add to Step 1.\n"
                         "   5. In another vessel: mix 142.50 g Titanium Dioxide and 62.50 g Purified Talc in 6.75 kg Isopropanol Alcohol; "
                         "pass through a fine sieve, pour into Step 1 while stirring."},
    {"num": "2", "desc": "Set coating equipment parameters:\n"
                         "   • Spray gun pressure: 2.0–2.25 kg/cm³\n"
                         "   • Storage tank pressure: 0.5–1.0 kg/cm³\n"
                         "   • Coating pan speed: 10–14 RPM\n"
                         "   • Hot air blower temperature: 80 ± 5°C\n"
                         "   • Tablet bed temperature: 40 ± 5°C\n"
                         "Record set value and actual reading for each parameter."},
    {"num": "3", "desc": "Load sorted tablets into the coating pan. Switch on hot air blower and adjust incoming air temperature to 80°C. "
                         "Jog tablets for 15 minutes by slow intermittent rotation until tablet bed temperature reaches 40–45°C."},
    {"num": "4", "desc": "Switch on exhaust fan. Start rotating pan. Position spray gun at centre of tablet bed, "
                         "about 1/3 of the height from the top of the falling tablet bed."},
    {"num": "5", "desc": "Spray the tablets with coating solution continuously until the solution is exhausted. "
                         "Do NOT rotate pan after coating solution is exhausted. "
                         "Note: Coating solution should not be kept for more than 24 hours."},
    {"num": "6", "desc": "Perform IPC at each lot: weight check (20 tablets × average weight), disintegration (NMT 30 min), "
                         "hardness (NLT 4 kg/cm²), and visual appearance check."},
    {"num": "7", "desc": "Cool tablets to approximately 40°C. Sprinkle Talcum powder (62.50 g per lot) while rotating for about 5 minutes."},
    {"num": "8", "desc": "Off-load coated tablets into double polythene-lined drums. Weigh and close tightly. "
                         "Record drum numbers, gross weight, tare weight and net weight."},
]

_BLISTER_STEPS = [
    {"num": "1", "desc": "Verify coated and sorted tablets released by QC from SMFPQ. Confirm tablet count and BMR reference."},
    {"num": "2", "desc": "Load base film: PVC Clear Film 206×0.25 mm. Load lid foil: Printed Aluminium Foil 203×0.25 mm (Trade or UG). "
                         "Verify foil AR number and expiry."},
    {"num": "3", "desc": "Set blister machine:\n"
                         "   • PVC clear film 206×0.25mm, Al foil 203×0.25mm\n"
                         "   • Pack size: 10 tablets per blister (10×10 blister pack = 100 tabs per unit carton)\n"
                         "   • Set and record sealing temperature, forming temperature and machine speed."},
    {"num": "4", "desc": "Set coding / embossing: Batch No., Manufacturing Date, Expiry Date. "
                         "Attach first coded sample to BMR. "
                         "Packing Supervisor approves coding. QA Officer approves coded sample."},
    {"num": "5", "desc": "Run batch blistering. Perform IPC every 1 hour: "
                         "foil appearance and printed details, leak test (no staining), blister formation (size, centering, knurling clarity, coding clarity)."},
    {"num": "6", "desc": "Complete batch. Count total blisters. Transfer to secondary packing area. "
                         "Pack 10 blisters per unit carton (Trade: 10×10). Pack 150 unit cartons per corrugated shipping carton."},
    {"num": "7", "desc": "Reconcile aluminium foil, PVC film and blisters used vs issued. "
                         "Record rejects and reworkables separately."},
]

_SECONDARY_STEPS = [
    {"num": "1", "desc": "Check specimen of overprinted carton/monocarton, leaflet and shipper label attached to BMR; "
                         "confirmed checked and approved by QA Officer online."},
    {"num": "2", "desc": "Transfer overprinted packaging material from printing room to secondary packing room. "
                         "Check displayed details on cartons: Batch No., Mfg Date and Expiry Date as per BMR. Check carton overprinting intactness."},
    {"num": "3", "desc": "Verify leaflet/insert information is clear, legible and specific to Formin 500mg."},
    {"num": "4", "desc": "Open carton. Insert leaflet with number of blisters as specified in BMR (10 blisters per unit carton — 10×10 Trade). "
                         "Close carton. Arrange into shipper."},
    {"num": "5", "desc": "Once shipper is filled (150 unit cartons per shipper for Trade), insert packing slip signed by group leader. "
                         "Supervisor and QA officer sign packing slip and authorise sealing."},
    {"num": "6", "desc": "Seal shipper with KPI branded BOPP tape. Attach shipper label. Record exact loose-shipper quantity on shipper label."},
    {"num": "7", "desc": "Reconcile all printed cartons, leaflets, shipper boxes and remaining unused material. "
                         "Destroy any leftover printed cartons/labels in presence of QA Officer and record the number."},
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
        config={"beginning_items": _DISPENSING_BEGIN, "ending_items": _GENERIC_END},
        page=1,
    ))
    s.append(sec(
        "material_dispensing", "form",
        "Dispensing Record — Raw Materials",
        config={
            "description": (
                "Batch Size: 500,000 Tablets (2 lots). MFR No.: KPI/MFR/014/00. "
                "Record for each material: AR No., Unit Qty (mg/tablet), Overage, Total Qty (mg/tablet), "
                "Total Batch Quantity (kg), Lot Quantity, Tare/Gross/Net Weights, Balance ID, "
                "Weighed By, Checked By, Received By."
            ),
            "materials": [
                {"sr": "1",  "name": "Metformin Hydrochloride BP",   "ar_code": "MET1HN", "unit_qty_mg": "500.00", "total_batch_kg": "250.00", "lots": "2 × 125.00 kg"},
                {"sr": "2",  "name": "Povidone K-30 BP",             "ar_code": "PVP2XT", "unit_qty_mg": "26.485", "total_batch_kg": "13.24",  "lots": "2 × 6.62 kg"},
                {"sr": "3",  "name": "Microcrystalline Cellulose BP", "ar_code": "MCC2XN", "unit_qty_mg": "7.054",  "total_batch_kg": "3.53",   "lots": "2 × 1.765 kg"},
                {"sr": "4",  "name": "Croscarmellose Sodium BP",     "ar_code": "CMC2SN", "unit_qty_mg": "10.582", "total_batch_kg": "5.29",   "lots": "1 × 5.29 kg"},
                {"sr": "5",  "name": "Magnesium Stearate BP",        "ar_code": "MAG2SN", "unit_qty_mg": "3.527",  "total_batch_kg": "1.764",  "lots": "1 × 1.764 kg"},
                {"sr": "6",  "name": "Purified Talc BP",             "ar_code": "TAL2XN", "unit_qty_mg": "2.351",  "total_batch_kg": "1.176",  "lots": "1 × 1.176 kg"},
                {"sr": "7",  "name": "Hydroxypropylmethyl Cellulose BP (HPMC)", "ar_code": "HPC2X1", "unit_qty_mg": "4.00", "total_batch_kg": "2.00", "lots": "4 × 500.00 g"},
                {"sr": "8",  "name": "Propylene Glycol USP",         "ar_code": "MPG2XN", "unit_qty_mg": "0.53",   "total_batch_kg": "0.265",  "lots": "4 × 66.25 g"},
                {"sr": "9",  "name": "P.E.G. 6000 BP",               "ar_code": "PEG2XN", "unit_qty_mg": "0.60",   "total_batch_kg": "0.30",   "lots": "4 × 75.00 g"},
                {"sr": "10", "name": "Isopropyl Alcohol BP",         "ar_code": "IPA2XN", "unit_qty_mg": "90.00",  "total_batch_kg": "45.00",  "lots": "4 × 11.25 kg"},
                {"sr": "11", "name": "Methylene Chloride",           "ar_code": "MYC2XN", "unit_qty_mg": "156.00", "total_batch_kg": "78.00",  "lots": "4 × 19.50 kg"},
                {"sr": "12", "name": "Titanium Dioxide BP",          "ar_code": "TIO3XN", "unit_qty_mg": "1.14",   "total_batch_kg": "0.57",   "lots": "4 × 142.50 g"},
                {"sr": "13", "name": "Talcum BP (coating)",          "ar_code": "TAL2XN", "unit_qty_mg": "0.50",   "total_batch_kg": "0.25",   "lots": "4 × 62.50 g"},
                {"sr": "14", "name": "Talcum BP (polishing)",        "ar_code": "TAL2XN", "unit_qty_mg": "0.04",   "total_batch_kg": "0.02",   "lots": "4 × 5.00 g"},
            ],
            "totals": {
                "core_total_mg": "550.00 mg/tablet (uncoated)",
                "coating_total_mg": "252.81 mg/tablet equivalent (solvent + coating agents)",
                "avg_weight_uncoated": "550.0 mg",
                "avg_weight_coated": "556.81 mg",
                "dispensing_balances": "B-46, B-28, B-59 (dispensing); B-53 to B-55, B-23, B-52 (IPQC lab)",
            },
        },
        page=1,
    ))

    # ------------------------------------------------------------------ #
    # PHASE 2 — Granulation
    # ------------------------------------------------------------------ #
    s.append(sec(
        "granulation", "line_clearance",
        "Granulation Area Line Clearance",
        config={"beginning_items": _GRANULATION_BEGIN, "ending_items": _GENERIC_END},
        page=2,
    ))
    s.append(sec(
        "granulation", "process_steps",
        "Granulation Process Steps",
        config={
            "steps": _GRANULATION_STEPS,
            "has_timing": True,
            "equipment_list": [
                {"name": "Rapid Mixer Granulator (RMG) — Granulation 1", "id": "T-47"},
                {"name": "Rapid Mixer Granulator (RMG) — Granulation 2", "id": "T-27"},
                {"name": "Fluid Bed Dryer (FBD) — Granulation 1", "id": "T-48 / T-67"},
                {"name": "Fluid Bed Dryer (FBD) — Granulation 2", "id": "T-24 / T-26"},
                {"name": "Paste Kettle — Granulation 1", "id": "T-49"},
                {"name": "Paste Kettle — Granulation 2", "id": "T-60"},
                {"name": "Comminuting Mill — Granulation 1", "id": "T-50 / T-14"},
                {"name": "Comminuting Mill — Granulation 2", "id": "T-44 / T-01"},
                {"name": "Vibro Sifter — Granulation 1", "id": "T-77"},
                {"name": "Vibro Sifter — Granulation 2", "id": "T-78"},
                {"name": "Weighing Balance", "id": "B-60 / B-13"},
            ],
        },
        page=2,
    ))
    s.append(sec(
        "granulation", "qa_report",
        "Post-Granulation / Post-Drying Quality Check",
        config={
            "tests": [
                {"test": "Loss on Drying (LOD)", "spec": "1.0% – 4.0% w/w (tested at 105°C on IR moisture balance)"},
                {"test": "Sample quantity for LOD", "spec": "20 g of dried granules"},
                {"test": "Appearance of dried granules", "spec": "Free-flowing granules, white to off-white colour"},
                {"test": "Final milling sieve", "spec": "Comminuting Mill with sieve No. 2.5"},
            ],
            "has_comply": True,
            "next_stage": "Blending/Lubrication",
            "reject_note": "If LOD outside 1.0–4.0%, label RMG bowl as REJECTED/REWORK and send for reworking. Do NOT proceed.",
        },
        page=3,
    ))
    s.append(sec(
        "granulation", "yield_reconciliation",
        "Granulation Yield Reconciliation",
        config={
            "rows": [
                {"key": "A", "label": "Theoretical Batch Size with respect to dispensed material (kg)", "formula": ""},
                {"key": "B", "label": "Actual Quantities of Dried Granules (kg)", "formula": ""},
                {"key": "C", "label": "Sample Quantities — LOD / In-Process Checks (kg)", "formula": ""},
                {"key": "D", "label": "Validation Samples (kg)", "formula": ""},
                {"key": "E", "label": "Rejects, if any (kg)", "formula": ""},
                {"key": "F", "label": "Total Actual Yield [B + C + D]", "formula": "B+C+D"},
                {"key": "G", "label": "Unaccountable Losses [A − (E + F)]", "formula": "A-(E+F)"},
                {"key": "H", "label": "% Yield = F × 100 / A", "formula": "F/A*100"},
            ],
            "permissible": "98% – 102%",
        },
        page=3,
    ))

    # ------------------------------------------------------------------ #
    # PHASE 3 — Blending
    # ------------------------------------------------------------------ #
    s.append(sec(
        "blending", "line_clearance",
        "Blending/Lubrication Area Line Clearance",
        config={
            "beginning_items": [
                "Area cleaned as per SOP; previous product containers, materials and labels removed.",
                "Double Cone Blender (T-04 / T-09 / T-17) cleaned and 'CLEANED' labeled.",
                "Vibrosifter (T-66 / T-79) sieves clean and ready.",
                "Milled granules verified: correct AR, BMR reference, LOD 1.0–4.0%.",
                "Blending excipients (Croscarmellose Sodium, Purified Talc, Magnesium Stearate) weighed and AR verified.",
                "Balance calibration and verification records updated.",
                "Environmental conditions: Temperature NMT 28°C, RH 40–65%.",
            ],
            "ending_items": _GENERIC_END,
        },
        page=4,
    ))
    s.append(sec(
        "blending", "process_steps",
        "Blending/Lubrication Process Steps",
        config={
            "steps": _BLENDING_STEPS,
            "has_timing": True,
            "equipment_list": [
                {"name": "Double Cone Blender", "id": "T-04 / T-09 / T-17"},
                {"name": "Vibrosifter", "id": "T-66 / T-79"},
                {"name": "Weighing Balance", "id": "B-60 / B-13"},
            ],
        },
        page=4,
    ))
    s.append(sec(
        "blending", "qa_report",
        "Post-Blending Quality Check",
        config={
            "tests": [
                {"test": "LOD by IR Moisture Balance (Top sample)", "spec": "1.0% – 4.0%"},
                {"test": "LOD by IR Moisture Balance (Middle sample)", "spec": "1.0% – 4.0%"},
                {"test": "LOD by IR Moisture Balance (Bottom sample)", "spec": "1.0% – 4.0%"},
                {"test": "Blend Homogeneity (visual uniform appearance)", "spec": "Uniform, no lumps or segregation"},
            ],
            "has_comply": True,
            "next_stage": "Tablet Compression",
            "reject_note": "If LOD outside 1.0–4.0% or blend is non-uniform, label blender as REJECTED/REWORK. Do NOT proceed.",
        },
        page=4,
    ))
    s.append(sec(
        "blending", "yield_reconciliation",
        "Blending Yield Reconciliation",
        config={
            "rows": [
                {"key": "A", "label": "Theoretical Batch Size with respect to Dried Granules + Blending Materials (kg)", "formula": ""},
                {"key": "B", "label": "Actual Quantities of Lubricated Granules (kg)", "formula": ""},
                {"key": "C", "label": "Sample Quantities — LOD / In-Process Checks (kg)", "formula": ""},
                {"key": "D", "label": "Validation Samples (kg)", "formula": ""},
                {"key": "E", "label": "Rejects, if any (kg)", "formula": ""},
                {"key": "F", "label": "Total Actual Yield [B + C + D]", "formula": "B+C+D"},
                {"key": "G", "label": "Unaccountable Losses [A − (E + F)]", "formula": "A-(E+F)"},
                {"key": "H", "label": "% Yield = F × 100 / A", "formula": "F/A*100"},
            ],
            "permissible": "98% – 102%",
        },
        page=5,
    ))

    # ------------------------------------------------------------------ #
    # PHASE 4 — Compression
    # ------------------------------------------------------------------ #
    s.append(sec(
        "compression", "line_clearance",
        "Compression Area Line Clearance",
        config={"beginning_items": _COMPRESSION_BEGIN, "ending_items": _GENERIC_END},
        page=6,
    ))
    s.append(sec(
        "compression", "equipment_setup",
        "Compression Machine Setup",
        config={
            "machine": "Rotary Tablet Compression Machine (D-Tooling, 12.5mm round shallow concave)",
            "fields": [
                {"key": "machine_no", "label": "Machine No. (T-06/T-15/T-30/T-35/T-52/T-80)"},
                {"key": "tooling_type", "label": "Tooling Type (D-Tooling)"},
                {"key": "punch_size", "label": "Punch Size (12.5 mm)"},
                {"key": "punch_shape", "label": "Punch Shape (Shallow Concave, Plain — Upper & Lower)"},
                {"key": "no_of_stations", "label": "No. of Stations"},
                {"key": "nominal_weight", "label": "Nominal Tablet Weight (550.0 mg)"},
                {"key": "weight_t1_upper", "label": "Weight +T1 Upper (566.5 mg)"},
                {"key": "weight_t2_upper", "label": "Weight +T2 Alert (577.5 mg)"},
                {"key": "weight_t1_lower", "label": "Weight −T1 Lower (533.5 mg)"},
                {"key": "weight_t2_lower", "label": "Weight −T2 Alert (522.5 mg)"},
                {"key": "hardness_spec", "label": "Hardness Spec (NLT 3 kg/cm²)"},
                {"key": "thickness_spec", "label": "Thickness Spec (5.00 ± 0.3 mm)"},
                {"key": "diameter_spec", "label": "Diameter Spec (12.5 ± 0.1 mm)"},
                {"key": "disintegration_spec", "label": "Disintegration (NMT 15 min)"},
                {"key": "friability_spec", "label": "Friability (NMT 1.0%)"},
                {"key": "machine_speed", "label": "Machine Speed (rpm)"},
                {"key": "setup_operator", "label": "Setup Operator"},
                {"key": "setup_supervisor", "label": "Checked by Section Supervisor"},
                {"key": "setup_qa", "label": "Verified by QA"},
            ],
        },
        page=6,
    ))
    s.append(sec(
        "compression", "process_steps",
        "Compression Process Steps",
        config={
            "steps": _COMPRESSION_STEPS,
            "has_timing": True,
            "equipment_list": [
                {"name": "Compression Machine", "id": "T-06 / T-15 / T-30 / T-35 / T-52 / T-80"},
                {"name": "Metal Detector", "id": "T-84 / T-85"},
                {"name": "De-duster", "id": "T-86 / T-87"},
            ],
        },
        page=6,
    ))

    # Production IPC sheets
    for n in range(1, 6):
        s.append(sec(
            "compression", "ipc_table",
            f"Compression In-Process Control — Production Sheet {n}",
            config={
                "sheet_number": n,
                "ipc_type": "production",
                "frequency": "Initially + Every 60 minutes",
                "header_fields": [
                    {"key": "appearance", "label": "Physical Appearance"},
                    {"key": "group_weight", "label": "Group Weight 20 tabs (mg)"},
                    {"key": "avg_weight", "label": "Average Weight (mg) | Target: 550.0 mg"},
                    {"key": "weight_max", "label": "Max Wt (mg) | Alert+T2: 577.5"},
                    {"key": "weight_min", "label": "Min Wt (mg) | Alert−T2: 522.5"},
                    {"key": "hardness", "label": "Hardness (kg/cm²) | NLT 3"},
                    {"key": "thickness", "label": "Thickness (mm) | 5.00 ± 0.3"},
                    {"key": "diameter", "label": "Diameter (mm) | 12.5 ± 0.1"},
                    {"key": "disintegration", "label": "Disintegration (min) | NMT 15"},
                    {"key": "friability", "label": "Friability (%) | NMT 1.0"},
                ],
            },
            page=7,
        ))

    # QA IPC sheets
    for n in range(1, 3):
        s.append(sec(
            "compression", "ipc_table",
            f"Compression In-Process Control — QA Sheet {n}",
            config={
                "sheet_number": n,
                "ipc_type": "qa",
                "frequency": "Start / Mid / End of batch",
            },
            page=8,
        ))

    s.append(sec(
        "compression", "yield_reconciliation",
        "Compression Yield Reconciliation",
        config={
            "rows": [
                {"key": "A", "label": "Theoretical Batch Size with respect to Blended Granules (kg)", "formula": ""},
                {"key": "B", "label": "Actual Quantities of Tablets Compressed (kg)", "formula": ""},
                {"key": "C", "label": "Sample Quantities — In-Process Checks (kg)", "formula": ""},
                {"key": "D", "label": "Validation Samples (kg)", "formula": ""},
                {"key": "E", "label": "Rejects, if any (kg)", "formula": ""},
                {"key": "F", "label": "Total Actual Yield [B + C + D]", "formula": "B+C+D"},
                {"key": "G", "label": "Unaccountable Losses [A − (E + F)]", "formula": "A-(E+F)"},
                {"key": "H", "label": "% Yield = F × 100 / A", "formula": "F/A*100"},
            ],
            "permissible": "98% – 102%",
        },
        page=9,
    ))

    # ------------------------------------------------------------------ #
    # PHASE 5 — Post-Compression QC
    # ------------------------------------------------------------------ #
    s.append(sec(
        "post_compression_qc", "qa_report",
        "Post-Compression Quality Control Report",
        config={
            "tests": [
                {"test": "Physical Appearance", "spec": "White round biconvex uncoated tablets, plain on both sides"},
                {"test": "Diameter (mm)", "spec": "12.5 ± 0.1 mm"},
                {"test": "Thickness (mm)", "spec": "5.00 ± 0.3 mm"},
                {"test": "Average Tablet Weight (mg)", "spec": "550.0 ± 2% (range: 539.0 – 561.0 mg)"},
                {"test": "Weight Uniformity", "spec": "±5% of average. NMT 2 tablets outside 5% range; none outside 10% range"},
                {"test": "Hardness (kg/cm²)", "spec": "NLT 3 kg/cm²"},
                {"test": "Friability", "spec": "NMT 1.0%. If obviously cleaved/cracked/chipped/broken tablets present — FAIL"},
                {"test": "Disintegration Time", "spec": "NMT 15 minutes"},
                {"test": "Assay — Metformin HCl (HPLC)", "spec": "95.0%–105.0% of label claim (500 mg)"},
                {"test": "Dissolution (BP)", "spec": "NLT 70% for each tablet"},
            ],
            "has_comply": True,
            "next_stage": "Sorting → Film Coating",
            "reject_note": (
                "If any test fails, quarantine batch, label 'REJECTED / REWORK' and raise Deviation Report. "
                "Do NOT proceed to sorting or coating."
            ),
        },
        page=10,
    ))
    s.append(sec(
        "post_compression_qc", "form",
        "Post-Compression QC Decision",
        config={
            "description": (
                "QC Officer to record test results, sign and indicate APPROVED / REJECTED. "
                "Production Manager and QA Manager counter-sign before batch is released to sorting."
            ),
        },
        page=10,
    ))

    # ------------------------------------------------------------------ #
    # PHASE 6 — Sorting
    # ------------------------------------------------------------------ #
    s.append(sec(
        "sorting", "line_clearance",
        "Sorting / Visual Inspection Area Line Clearance",
        config={
            "beginning_items": [
                "Sorting area clean and clear of previous batch / product.",
                "Light boxes / inspection lamps clean and functional.",
                "Rejection containers labeled 'REJECTED TABLETS'.",
                "Core tablets brought to sorting with correct BMR reference and count.",
                "Sorting personnel trained and gowned.",
            ],
            "ending_items": _GENERIC_END,
        },
        page=11,
    ))
    s.append(sec(
        "sorting", "process_steps",
        "Sorting / Visual Inspection Steps",
        config={
            "steps": _SORTING_STEPS,
            "has_timing": True,
        },
        page=11,
    ))
    s.append(sec(
        "sorting", "yield_reconciliation",
        "Sorting Yield Reconciliation",
        config={
            "rows": [
                {"key": "A", "label": "No. of Core Tablets Received from Compression", "formula": ""},
                {"key": "B", "label": "No. of Good Tablets Accepted", "formula": ""},
                {"key": "C", "label": "No. Rejected — Capped / Broken", "formula": ""},
                {"key": "D", "label": "No. Rejected — Chipped / Mottled", "formula": ""},
                {"key": "E", "label": "No. Rejected — Other defects", "formula": ""},
                {"key": "F", "label": "Total Rejected  [C + D + E]", "formula": "C+D+E"},
                {"key": "G", "label": "% Yield  [B ÷ A × 100]", "formula": "B/A*100"},
            ],
            "permissible": "NLT 97.0%",
        },
        page=11,
    ))

    # ------------------------------------------------------------------ #
    # PHASE 7 — Coating
    # ------------------------------------------------------------------ #
    s.append(sec(
        "coating", "line_clearance",
        "Coating Area Line Clearance",
        config={"beginning_items": _COATING_BEGIN, "ending_items": _GENERIC_END},
        page=12,
    ))
    s.append(sec(
        "coating", "equipment_setup",
        "Film Coating Machine Setup",
        config={
            "machine": "Coating Pan (hot air blower-type; spray gun nozzle diameter 1.0 mm)",
            "fields": [
                {"key": "coating_machine", "label": "Coating Machine No."},
                {"key": "spray_gun_pressure", "label": "Spray Gun Pressure (Set: 2.0–2.25 kg/cm³)"},
                {"key": "storage_tank_pressure", "label": "Storage Tank Pressure (Set: 0.5–1.0 kg/cm³)"},
                {"key": "pan_speed", "label": "Coating Pan Speed (Set: 10–14 RPM)"},
                {"key": "inlet_temp", "label": "Hot Air Blower Temperature (Set: 80 ± 5°C)"},
                {"key": "tablet_bed_temp", "label": "Tablet Bed Temperature (Set: 40 ± 5°C)"},
                {"key": "lots_total", "label": "Total Coating Lots (4 lots for this batch)"},
                {"key": "methylene_chloride_per_lot", "label": "Methylene Chloride per lot (19.50 kg = 16.50 + 3.0 kg)"},
                {"key": "ipa_per_lot", "label": "Isopropanol Alcohol per lot (11.25 kg = 4.50 + 6.75 kg)"},
                {"key": "hpmc_per_lot", "label": "HPMC per lot (500.00 g)"},
                {"key": "peg_per_lot", "label": "PEG 6000 per lot (75.00 g)"},
                {"key": "propylene_glycol_per_lot", "label": "Propylene Glycol per lot (66.25 g)"},
                {"key": "titanium_dioxide_per_lot", "label": "Titanium Dioxide per lot (142.50 g)"},
                {"key": "talc_per_lot", "label": "Purified Talc (coating) per lot (62.50 g)"},
                {"key": "talc_polishing_per_lot", "label": "Talc for Polishing per lot (5.00 g)"},
                {"key": "setup_operator", "label": "Done by Operator"},
                {"key": "setup_supervisor", "label": "Checked by SPV"},
                {"key": "setup_qa", "label": "Verified by QA"},
            ],
        },
        page=12,
    ))
    s.append(sec(
        "coating", "process_steps",
        "Film Coating Process Steps",
        config={
            "steps": _COATING_STEPS,
            "has_timing": True,
        },
        page=12,
    ))

    # Coating IPC sheets (4 lots)
    for n in range(1, 3):
        s.append(sec(
            "coating", "ipc_table",
            f"Coating In-Process Control — Sheet {n} (Lots {(n-1)*2+1} & {(n-1)*2+2})",
            config={
                "sheet_number": n,
                "ipc_type": "production",
                "frequency": "Per lot; at end of each lot",
                "header_fields": [
                    {"key": "lot_number", "label": "Lot Number"},
                    {"key": "avg_weight", "label": "Average Weight (mg) | Target: 556.81 mg coated"},
                    {"key": "max_weight", "label": "Max Weight (mg)"},
                    {"key": "min_weight", "label": "Min Weight (mg)"},
                    {"key": "disintegration", "label": "Disintegration (min) | NMT 30 min"},
                    {"key": "hardness", "label": "Hardness (kg/cm²) | NLT 4"},
                    {"key": "appearance", "label": "Physical Appearance"},
                ],
            },
            page=13,
        ))

    s.append(sec(
        "coating", "qa_report",
        "Post-Coating Quality Check",
        config={
            "tests": [
                {"test": "Physical Appearance", "spec": "White, smooth, uniformly coated round biconvex tablets"},
                {"test": "Average Weight (Coated)", "spec": "556.81 mg (uncoated 550.0 mg + 6.81 mg coating)"},
                {"test": "Hardness (kg/cm²)", "spec": "NLT 4 kg/cm²"},
                {"test": "Disintegration (coated)", "spec": "NMT 30 minutes"},
                {"test": "Appearance uniformity", "spec": "No picking, sticking, colour variation or rough surface"},
            ],
            "has_comply": True,
            "next_stage": "Sorting (Post-Coat) → Blister Packing",
            "reject_note": "If appearance or weight fails, quarantine and raise Deviation Report.",
        },
        page=13,
    ))
    s.append(sec(
        "coating", "yield_reconciliation",
        "Coating Yield Reconciliation",
        config={
            "rows": [
                {"key": "A", "label": "No. of Core Tablets Loaded into Pan", "formula": ""},
                {"key": "B", "label": "Weight of Core Tablets Charged (kg)", "formula": ""},
                {"key": "C", "label": "Weight of Coated Tablets Discharged (kg)", "formula": ""},
                {"key": "D", "label": "Actual Weight Gain (kg)  [C − B]", "formula": "C-B"},
                {"key": "E", "label": "% Weight Gain  [D ÷ B × 100]", "formula": "D/B*100"},
                {"key": "F", "label": "No. of Coated Tablets (Good)", "formula": ""},
                {"key": "G", "label": "No. Rejected (picking / chipping during coating)", "formula": ""},
                {"key": "H", "label": "% Yield by count  [F ÷ A × 100]", "formula": "F/A*100"},
            ],
            "permissible": "NLT 97.0% (by count)",
        },
        page=14,
    ))

    # ------------------------------------------------------------------ #
    # PHASE 8 — Blister Packing
    # ------------------------------------------------------------------ #
    s.append(sec(
        "blister_packing", "line_clearance",
        "Blister Packing Area Line Clearance",
        config={"beginning_items": _BLISTER_BEGIN, "ending_items": _GENERIC_END},
        page=15,
    ))
    s.append(sec(
        "blister_packing", "process_steps",
        "Blister Packing Process Steps",
        config={
            "steps": _BLISTER_STEPS,
            "has_timing": True,
            "equipment_list": [
                {"name": "Blister Machine", "id": "P-03 / P-10 / P-20 / P-21 / P-27"},
                {"name": "Metal Detector", "id": ""},
            ],
        },
        page=15,
    ))

    for n in range(1, 4):
        s.append(sec(
            "blister_packing", "ipc_table",
            f"Blister Packing IPC — Sheet {n}",
            config={
                "sheet_number": n,
                "ipc_type": "production",
                "frequency": "At start, beginning of each shift/resumption, every 1 hour",
                "header_fields": [
                    {"key": "foil_appearance", "label": "Foil Appearance & Printed Details"},
                    {"key": "leak_test", "label": "Leak Test (no staining) | sealing roller temp (°C)"},
                    {"key": "blister_formation", "label": "Blister Formation: centered, correct size"},
                    {"key": "knurling", "label": "Knurling clearly visible"},
                    {"key": "coding_batch", "label": "Batch No. clear and correct"},
                    {"key": "coding_dates", "label": "Mfg Date / Exp Date correct"},
                ],
            },
            page=16,
        ))

    s.append(sec(
        "blister_packing", "yield_reconciliation",
        "Blister Packing Yield Reconciliation",
        config={
            "rows": [
                {"key": "A", "label": "Theoretical Batch Size (Blisters) with respect to tablets received from sorting", "formula": ""},
                {"key": "B", "label": "Actual Quantities of Blisters (good)", "formula": ""},
                {"key": "C", "label": "Sample Quantities — In-Process Checks", "formula": ""},
                {"key": "D", "label": "Validation Samples", "formula": ""},
                {"key": "E", "label": "Rejects, if any", "formula": ""},
                {"key": "F", "label": "Total Actual Yield [B + C + D]", "formula": "B+C+D"},
                {"key": "G", "label": "Unaccountable Losses [A − (E + F)]", "formula": "A-(E+F)"},
                {"key": "H", "label": "% Yield = F × 100 / A", "formula": "F/A*100"},
            ],
            "permissible": "98% – 102%",
        },
        page=17,
    ))

    # ------------------------------------------------------------------ #
    # PHASE 9 — Secondary Packaging
    # ------------------------------------------------------------------ #
    s.append(sec(
        "secondary_packaging", "line_clearance",
        "Secondary Packing Area Line Clearance",
        config={
            "beginning_items": [
                "Previous batch fully cleared from packing area.",
                "Cartons, leaflets, shipper boxes verified (Batch No., Mfg, Expiry match BMR).",
                "Coding machine programmed and sample approved by QA.",
                "Environmental conditions within specification.",
                "Packing records available and open at packing station.",
            ],
            "ending_items": _GENERIC_END,
        },
        page=18,
    ))
    s.append(sec(
        "secondary_packaging", "process_steps",
        "Secondary Packing Process Steps",
        config={"steps": _SECONDARY_STEPS, "has_timing": True},
        page=18,
    ))
    s.append(sec(
        "secondary_packaging", "coding_control",
        "Coding Control and Reconciliation",
        config={
            "coding_fields": [
                {"key": "batch_no", "label": "Batch No. coded on carton / blister / foil"},
                {"key": "mfg_date", "label": "Manufacturing Date (Mfg. Date)"},
                {"key": "exp_date", "label": "Expiry Date (Exp. Date)"},
                {"key": "items_coded", "label": "Items coded (mark): Labels / Unit Cartons / Shipper Labels / Blisters / Others"},
                {"key": "coding_stamp_set", "label": "Coding Stamp Set by (Operator) — Sign & Date"},
                {"key": "coding_machine_no", "label": "Coding Machine Number"},
                {"key": "first_sample_attached", "label": "First coded sample + PIL attached to BMR (Yes/No)"},
                {"key": "approved_packaging_spv", "label": "Coding Approved by Packing Supervisor — Sign & Date"},
                {"key": "approved_qa", "label": "Coding Approved by QA Officer — Sign & Date"},
            ],
            "packer_count": 9,
            "reconcile_fields": [
                {"key": "item_name", "label": "Name of Item"},
                {"key": "items_issued", "label": "No. of Item Issued"},
                {"key": "items_coded", "label": "No. of Item Coded"},
                {"key": "items_uncoded", "label": "No. of Item Uncoded"},
                {"key": "items_damaged", "label": "No. of Items Damaged / Rejected during Coding"},
                {"key": "items_used", "label": "No. of Items Used"},
                {"key": "items_excess", "label": "No. of Excess Items, if any"},
                {"key": "items_destroyed", "label": "No. of Items to be Destroyed (with QA consent)"},
                {"key": "reconciliation_approved", "label": "Reconciliation Approved by QA — Sign & Date"},
            ],
        },
        page=19,
    ))
    for n in range(1, 4):
        s.append(sec(
            "secondary_packaging", "ipc_table",
            f"Secondary Packing IPC Check — Sheet {n}",
            config={
                "sheet_number": n,
                "ipc_type": "production",
                "frequency": "Every 1 Hour",
                "header_fields": [
                    {"key": "reference_code", "label": "Reference code, product name and strength on carton labels"},
                    {"key": "batch_mfg_exp", "label": "Batch No., Mfg Date, Exp Date on cartons — correct (Yes/No)"},
                    {"key": "pack_size", "label": "Pack size on carton (10×10 / 500’s / 1000’s)"},
                    {"key": "insert_present", "label": "Presence of PIL insert (Yes/No)"},
                    {"key": "insert_legible", "label": "Insert legible and clear (Yes/No)"},
                    {"key": "blisters_per_carton", "label": "No. of blisters/strips in carton correct (Yes/No)"},
                    {"key": "shipper_cartons", "label": "Shipper: correct no. of unit cartons (150 per shipper)"},
                    {"key": "sealing_done", "label": "Shipper sealed with KPI BOPP tape (Yes/No)"},
                ],
            },
            page=19,
        ))
    s.append(sec(
        "secondary_packaging", "yield_reconciliation",
        "Secondary Packing Yield Reconciliation",
        config={
            "rows": [
                {"key": "A", "label": "No. of Intact Shippers Packed", "formula": ""},
                {"key": "B", "label": "No. of Cartons in Intact Shippers [A × cartons per shipper]", "formula": ""},
                {"key": "C", "label": "Loose Quantity Packed (cartons/jars)", "formula": ""},
                {"key": "D", "label": "Total Quantity Packed [B + C]", "formula": "B+C"},
                {"key": "E", "label": "No. of Cartons Rejected (damaged/misprinted)", "formula": ""},
                {"key": "F", "label": "No. of Cartons Returned to Store", "formula": ""},
                {"key": "G", "label": "Cartons Issued from Store", "formula": ""},
                {"key": "H", "label": "Balance [G − D − E − F] (should = 0 or account for destroyed)", "formula": "G-D-E-F"},
            ],
            "permissible": "98% – 102%",
        },
        page=20,
    ))

    return s
