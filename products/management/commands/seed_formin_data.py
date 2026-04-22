"""
Seed product fields and equipment entries for FORMIN (id=15):
  FORMIN — Metformin Hydrochloride Tablets BP 500mg (Coated)
"""
from django.core.management.base import BaseCommand
from products.models import Product
from bmr.models import EquipmentEntry


# ── Equipment entries for FORMIN ──────────────────────────────────────────────
EQUIPMENT = {
    'dispensing': [
        ('Weighing Balance', 'B-46'),
        ('Weighing Balance', 'G-28'),
        ('Weighing Balance', 'B-59'),
        ('RLAF Booth',       'LAF-01'),
        ('RLAF Booth',       'LAF-05'),
    ],
    'granulation_1': [
        ('Rapid Mixer Granulator',  'T-47'),
        ('Fluidized Bed Dryers',    'T-48'),
        ('Fluidized Bed Dryers',    'T-67'),
        ('Vibro Sifter',            'T-77'),
        ('Paste Kettle',            'T-49'),
        ('Comminuting Mill',        'T-50'),
        ('Comminuting Mill',        'T-14'),
        ('Weighing Balance',        'B-60'),
    ],
    'granulation_2': [
        ('Rapid Mixer Granulator',  'T-27'),
        ('Fluidized Bed Dryers',    'T-24'),
        ('Fluidized Bed Dryers',    'T-26'),
        ('Vibro Sifter',            'T-78'),
        ('Paste Kettle',            'T-60'),
        ('Multimill',               'T-44'),
        ('Comminuting Mill',        'T-01'),
        ('Weighing Balance',        'B-13'),
    ],
    'blending': [
        ('Double Cone Blender', 'T-09'),
        ('Double Cone Blender', 'T-17'),
        ('Double Cone Blender', 'T-04'),
        ('Vibrosifter',         'T-66'),
        ('Vibrosifter',         'T-79'),
    ],
    'compression': [
        ('Compression Machine', 'T-06'),
        ('Compression Machine', 'T-15'),
        ('Compression Machine', 'T-30'),
        ('Compression Machine', 'T-35'),
        ('Compression Machine', 'T-52'),
        ('Compression Machine', 'T-80'),
    ],
    'film_coating': [
        ('Auto Coater',         'T-46'),
        ('Auto Coater',         'T-73'),
        ('Coating Pan',         'T-74'),
        ('Air Compressor',      'T-51'),
        ('Weighing Balance',    'B-60'),
        ('Stainless Steel Vessel', '—'),
    ],
    'ipqc_lab': [
        ('Weighing Balance',          'B-53'),
        ('Weighing Balance',          'B-54'),
        ('Weighing Balance',          'B-55'),
        ('Weighing Balance',          'B-23'),
        ('Weighing Balance',          'B-52'),
        ('IR Moisture Analyzer',      'B-19'),
        ('IR Moisture Analyzer',      'B-43'),
        ('Friability Apparatus',      'QD-075'),
        ('Friability Apparatus',      'T-33'),
        ('Hardness Tester',           'QD-081'),
        ('Hardness Tester',           'QD-073'),
        ('Disintegration Apparatus',  'QD-084'),
        ('Disintegration Apparatus',  'QD-085'),
        ('Vernier Caliper',           'QD-086'),
        ('Vernier Caliper',           'QD-087'),
        ('Leak Test Apparatus',       'QD-088'),
        ('Friability Apparatus',      'QD-077'),
    ],
    'visual_inspection': [
        ('Metal Detector', '—'),
        ('De-duster',      '—'),
    ],
    'blister_packing': [
        ('Blister Machine', 'P-03'),
        ('Blister Machine', 'P-10'),
        ('Blister Machine', 'P-20'),
        ('Blister Machine', 'P-21'),
        ('Blister Machine', 'P-27'),
    ],
    'strip_packing': [
        ('Strip Packing Machine', '—'),
    ],
}


# ── FORMIN product field values ────────────────────────────────────────────────
FORMIN_FIELDS = {
    # Identity
    'mfg_license_number':                  'NDA/MAL/HDP/1701',
    'shelf_life_years':                    2,

    # Tablet appearance
    'tablet_appearance_trade': (
        "White, round, flat, beveled Film Coated Tablets engraved 'P500' above "
        "and 'KPI' below the break line on one side and plain on the other."
    ),
    'tablet_appearance_ug': (
        "White, round, flat, beveled Film Coated Tablets engraved 'UG' above "
        "and 'KPI' below the break line on one side and plain on the other."
    ),

    # Compression specifications
    'average_weight_uncoated':             550.0,
    'average_weight_coated':               556.81,
    'standard_weight_tolerance_percentage': 2.0,
    'diameter_nominal':                    12.5,
    'diameter_tolerance':                  0.10,
    'thickness_nominal':                   5.00,
    'thickness_tolerance':                 0.30,
    'hardness_min':                        3.0,     # NLT 3 kg/cm² (uncoated, at compression)
    'coating_hardness_min':                4.0,     # NLT 4 kg/cm² (post-coating)
    'friability_max':                      1.0,
    'disintegration_time_max':             15.0,    # NMT 15 min (uncoated)
    'coating_disintegration_max':          30.0,    # NMT 30 min (post-coating)
    'dissolution_spec':                    'NLT 70% for each Tablet',
    'assay_min_percentage':                95.0,
    'assay_max_percentage':                105.0,

    # Granulation
    'granulation_lot_count':               2,
    'milling_sieve_size':                  2.5,
    'lod_limits':                          '1.0-4.0',

    # Blending (two-step)
    'magnesium_stearate_qty':              '1.764kg',
    'sieve_size_lubrication':              '#40',
    'blending_time':                       '15 minutes',   # step without Mg Stearate
    'blending_without_mag_time':           '15 minutes',
    'lubrication_with_mag_time':           '5 minutes',

    # Punch / tablet markings
    'punch_size':                          12.5,
    'punch_type':                          'D-TOOLING',
    'upper_punch_description': (
        "Round Flat Beveled, Embossed 'P500' over B/L and 'KPI' under B/L on one side"
    ),
    'lower_punch_description':             "Round Flat Beveled, Plain",

    # Film Coating settings
    'coating_lot_count':                   4,
    'coating_pan_speed':                   '10-14 RPM',
    'coating_hot_air_temp':                '80 \u00b1 5\u00b0C',        # 80 ± 5°C
    'coating_tablet_bed_temp':             '40 \u00b1 5\u00b0C',        # 40 ± 5°C
    'coating_spray_pressure':              '2.0-2.25 kg/cm\u00b3',      # kg/cm³
    'coating_storage_pressure':            '0.5-1.0 kg/cm\u00b3',

    # Coating solution preparation (5 steps)
    'coating_solution_instructions': [
        "Measure 16.50 kg of Methylene Chloride in a clean stainless steel vessel and keep aside.",
        "In a separate clean SS vessel, measure 3.0 kg of Methylene Chloride and dissolve 75.00 g of "
        "Polyethylene Glycol 6000 BP (PEG 6000) in it. Add this solution to the main vessel from step 1.",
        "Weigh 66.25 g of Propylene Glycol BP and add it to the main vessel from step 1 while stirring.",
        "In a clean SS vessel, measure 4.50 kg of Isopropyl Alcohol (IPA) and add 500.00 g of HPMC BP. "
        "Mix to form a smooth slurry. Add the slurry to the main vessel from step 1.",
        "In a clean SS vessel, measure 6.75 kg of IPA and add 142.50 g of Titanium Dioxide BP and "
        "62.50 g of Purified Talc BP. Pass through a fine sieve and add to the main vessel from step 1. "
        "Stir the complete dispersion continuously throughout the coating process.",
    ],

    # Granulation process instructions
    'dry_mixing_instructions': [
        "In a clean, dry stainless steel Rapid Mixer Granulator, add in sequence:<br>"
        "I. Metformin Hydrochloride BP (weighed quantity per lot)<br>"
        "II. Microcrystalline Cellulose BP<br>"
        "III. Pregelatinised Starch BP",
        "Dry-blend at SLOW speed for 10 minutes, then at FAST speed for 5 minutes.",
    ],
    'wet_mixing_instructions': [
        "Prepare binder solution: dissolve Povidone K30 BP in the required quantity of Purified Water BP "
        "in a clean stainless steel vessel. Stir until clear.",
        "Add the binder solution gradually to the dry-blended materials in the RMG while running at SLOW "
        "speed. After complete addition, mix at SLOW speed for 3 minutes, then FAST speed for 3 minutes "
        "until a uniform wet mass is formed.",
        "Discharge the wet granules onto stainless steel trays for drying.",
    ],
    'drying_instructions': [
        "Dry the wet granules in a Fluidized Bed Dryer (FBD) at 70\u00b0C for 45 minutes. Remove, turn the "
        "granules with a SS scoop, and continue drying.",
        "Repeat the above procedure until the LOD reading is within range (1.0-4.0%). "
        "Mill the partially dried granules through a Comminuting Mill fitted with a 4mm SS sieve. "
        "Re-dry as necessary.",
    ],
    'final_drying_instructions': [
        "Allow the granules to cool to room temperature, then pass them through a Comminuting Mill "
        "fitted with a 2.5 mm SS sieve. Check L.O.D on IR Moisture Balance at 105\u00b0C "
        "(Limit: 1.0\u20134.0% w/w).",
    ],

    # Line clearance items (dispensing)
    'dispensing_clearance_start_items': [
        "Ensure area is clean and no remnants of previous batch",
        "Verify weighing balance calibration is current",
        "Check RLAF is functioning and within pressure limits",
        "Confirm all containers and equipment are labelled correctly",
        "Verify temperature (NMT 28°C) and relative humidity (40-65%) of dispensing area",
    ],
    'dispensing_clearance_end_items': [
        "All dispensed materials are correctly labelled and covered",
        "Weighing records are complete and signed by operator and checker",
        "Dispensing area cleaned and cleared of all previous batch materials",
        "Containers transferred to granulation area",
    ],

    # Line clearance items (granulation)
    'granulation_clearance_start_items': [
        "Area free from previous batch materials and labels",
        "RMG cleaned and dried; check with UV lamp",
        "FBD bags checked for integrity",
        "All equipment coded and ready for use",
        "Environmental check: Temperature NMT 28°C, RH 40-65%",
    ],
    'granulation_clearance_end_items': [
        "Granules discharged, labelled and transferred",
        "All equipment cleaned after use",
        "Batch records updated and signed",
    ],

    # Line clearance items (blending)
    'blending_clearance_start_items': [
        "Area free from previous batch materials",
        "Double Cone Blender clean and dry; check with UV lamp",
        "Vibrosifter cleaned and correct sieve mesh fitted",
        "Environmental check: Temperature NMT 28°C, RH 40-65%",
    ],
    'blending_clearance_end_items': [
        "Blended bulk discharged, labelled and transferred to compression area",
        "Blending equipment cleaned after use",
        "Blending records completed and signed",
    ],

    # Line clearance items (compression)
    'compression_clearance_start_items': [
        "Area free from previous batch materials and labels",
        "Compression machine cleaned and punches / dies checked",
        "Punch and die details recorded in batch record",
        "Environmental check: Temperature NMT 28°C, RH 40-65%",
        "De-duster and metal detector confirmed operational",
    ],
    'compression_clearance_end_items': [
        "Compressed tablets collected in labelled containers",
        "Punches and dies cleaned and returned to store",
        "Compression machine cleaned after use",
        "Batch records completed and signed",
    ],

    # Line clearance items (sorting / inspection before coating)
    'sorting_clearance_start_items': [
        "Area free from previous batch materials",
        "Inspection conveyor / light box cleaned",
        "Metal detector calibrated and functional",
        "Environmental check: Temperature NMT 28°C, RH 40-65%",
    ],
    'sorting_clearance_end_items': [
        "Inspected tablets transferred to film coating area in labelled containers",
        "Rejected tablets segregated and labelled",
        "Inspection records completed and signed",
    ],

    # Line clearance items (film coating)
    'coating_clearance_start_items': [
        "Area free from previous batch materials and labels",
        "Auto Coater (coating pan) cleaned and dried; bowl polished",
        "Spray gun nozzles cleaned and checked; atomiser air checked",
        "Coating solution preparation area clean and ready",
        "Environmental check: Temperature NMT 28°C, RH 40-65%",
        "Air supply pressure confirmed adequate",
    ],
    'coating_clearance_end_items': [
        "Coated tablets discharged into labelled containers and transferred",
        "Coating pan, spray guns and solution vessel cleaned after use",
        "Film coating records completed and signed by operator and QA",
        "Residual coating solution disposed per SOP",
    ],

    # Packing clearance
    'packing_clearance_start_items': [
        "Area free from previous batch materials and labels",
        "Blister machine cleaned and all previous foil / PVC removed",
        "Correct foil and PVC loaded and batch coding set",
        "Environmental check: Temperature NMT 28°C, RH 40-65%",
        "Batch/Expiry/MFG date codes verified and approved by QA",
    ],
    'packing_clearance_end_items': [
        "All blisters collected and transferred to secondary packing",
        "Blister machine cleaned after use",
        "Packing records completed and signed",
    ],

    # Compression instructions
    'compression_instructions': [
        "Set up and calibrate the compression machine as per the SOP.",
        "Set the target weight to 550 ± 11 mg (±2%). Collect initial 20 tablets and check average weight, "
        "hardness (NLT 3 kg/cm²), thickness (5.00 ± 0.3 mm), diameter (12.5 ± 0.1 mm) and disintegration "
        "(NMT 15 min) before commencing full production.",
        "Sample 20 tablets at each IPQC sampling interval and record all data on the IPQC sheet.",
        "Any out-of-specification result must be reported immediately to the Supervisor and QA.",
        "Rejected tablets must be segregated, labelled and recorded.",
    ],
}


class Command(BaseCommand):
    help = 'Seed product fields and equipment entries for FORMIN (id=15)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Overwrite existing equipment entries (deletes all first)',
        )

    def handle(self, *args, **options):
        # Try by ID first; fall back to name search so it works on any server
        product = (
            Product.objects.filter(id=15).first()
            or Product.objects.filter(product_name__icontains='formin').first()
        )
        if not product:
            self.stderr.write(self.style.ERROR('FORMIN product not found — aborting'))
            return

        # ── Update product fields ──────────────────────────────────────────
        for field, value in FORMIN_FIELDS.items():
            setattr(product, field, value)
        product.save()
        self.stdout.write(self.style.SUCCESS(f'Updated {len(FORMIN_FIELDS)} fields for {product.product_name} (id={product.id})'))

        # ── Seed equipment entries ─────────────────────────────────────────
        existing = EquipmentEntry.objects.filter(product=product).count()
        if existing and not options['overwrite']:
            self.stdout.write(
                self.style.WARNING(
                    f'  {existing} equipment entries already exist — '
                    'use --overwrite to replace them. Skipping equipment.'
                )
            )
        else:
            EquipmentEntry.objects.filter(product=product).delete()
            created = 0
            for phase, items in EQUIPMENT.items():
                for order, (name, eq_id) in enumerate(items, start=1):
                    EquipmentEntry.objects.create(
                        product=product,
                        phase=phase,
                        equipment_name=name,
                        equipment_id=eq_id,
                        order=order,
                    )
                    created += 1
            self.stdout.write(self.style.SUCCESS(f'  Created {created} equipment entries for FORMIN'))

        self.stdout.write(self.style.SUCCESS('Done — FORMIN data seeded successfully.'))
