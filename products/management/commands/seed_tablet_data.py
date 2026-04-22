"""
Seed product fields and equipment entries for tablet products:
  - KAMADOL (id=13): Paracetamol Tablets BP 500mg
  - KAMSIDAR (id=11): Sulfadoxine and Pyrimethamine Tablets USP 525mg
"""
from django.core.management.base import BaseCommand
from products.models import Product
from bmr.models import EquipmentEntry


# ── Equipment that is identical for both tablet products ──────────────────────
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
    'compression': [
        ('Compression Machine', 'T-06'),
        ('Compression Machine', 'T-15'),
        ('Compression Machine', 'T-30'),
        ('Compression Machine', 'T-35'),
        ('Compression Machine', 'T-52'),
        ('Compression Machine', 'T-80'),
    ],
    'blending': [
        ('Double Cone Blender', 'T-09'),
        ('Double Cone Blender', 'T-17'),
        ('Double Cone Blender', 'T-04'),
        ('Vibrosifter',         'T-66'),
        ('Vibrosifter',         'T-79'),
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

# ── Per-product field values ───────────────────────────────────────────────────
# Name-based lookup map — works regardless of DB primary key
PRODUCT_NAME_MAP = {
    13: 'kamadol',   # fallback label used for name lookup
    11: 'kamsidar',
}

PRODUCTS = {
    13: {  # KAMADOL — Paracetamol Tablets BP 500mg
        'mfg_license_number':                  'NDA/MAL/HDP/1887',
        'average_weight_uncoated':             591.1,
        'tablet_appearance_trade':             "White round flat tablets embossed 'P500' above and 'KPI' below the break line on one side and plain on the other.",
        'tablet_appearance_ug':                "White round flat tablets embossed 'UG' above and 'KPI' below the break line on one side and plain on the other.",
        'diameter_nominal':                    12.50,
        'diameter_tolerance':                  0.20,
        'thickness_nominal':                   4.35,
        'thickness_tolerance':                 0.30,
        'magnesium_stearate_qty':              '256gm',
        'sieve_size_lubrication':              '#40',
        'blending_time':                       '20 minutes',
        'standard_weight_tolerance_percentage': 2.0,
        # Granulation instructions (Page 10-11 of official BMR)
        'dry_mixing_instructions': [
            "In clean stainless steel Rapid Mixer Granulator, add in sequence:<br>I. 100kg of Paracetamol<br>II. 10kg of Maize Starch",
            "Dry blend at SLOW speed in Rapid Mixer Granulator for 10 minutes then at FAST speed for 5 minutes.",
        ],
        'wet_mixing_instructions': [
            "Boil 25.0 litres of purified Water in stainless steel vessel.",
            "Meanwhile, add in sequence in a clean stainless steel mixing vessel:<br>I. 8 litres of cold purified water<br>II. 150g of Methylparaben<br>III. 8kg of Maize Starch",
            "Mix until smooth uniform slurry forms.",
            "Add hot boiling water to the slurry while vigorously stirring. A smooth uniform paste forms.",
            "Add the paste in 6 to the dry blend in 2 and mix at SLOW speed for 3 minutes then at FAST speed for 3 minutes.",
        ],
        'drying_instructions': [
            "Dry the granules at 70°C for 45 minutes in Fluid Bed Drier then remove and turn around the granules with a stainless steel scoop. Repeat the above procedure then mill the granules in Comminuting Mill fitted with sieve size 4. Redry the granules at 70°C for 45 minutes.",
            "Repeat the above procedure for the rest of the lots.",
        ],
        'final_drying_instructions': [
            "Let the granules cool to room temperature then mill with Milling machine fitted with sieve No. 2.5. Check L.O.D on IR Balance at 105 °C (Limit 1&#8209;4 % w/w).",
        ],
    },
    11: {  # KAMSIDAR — Sulfadoxine and Pyrimethamine Tablets USP 525mg
        'mfg_license_number':                  'NDA/MAL/HDP/5467',
        'average_weight_uncoated':             674.58,
        'tablet_appearance_trade':             "White, round, flat, beveled tablets embossed 'F' on one side and double cross line on the other side.",
        'tablet_appearance_ug':                "White, round, flat tablets embossed 'UG' above and 'KPI' under B/L below the break-line on one side and double cross line on the other.",
        'diameter_nominal':                    12.50,
        'diameter_tolerance':                  0.20,
        'thickness_nominal':                   4.48,
        'thickness_tolerance':                 0.30,
        'magnesium_stearate_qty':              '3.60kg',
        'sieve_size_lubrication':              '#40',
        'blending_time':                       '15 minutes',
        'standard_weight_tolerance_percentage': 2.0,
        # Granulation instructions (Page 12 of official BMR)
        'dry_mixing_instructions': [
            "Pulverize each lot of Sulfadoxine and Pyrimethamine by passing through Multimill fitted with 0.5mm S.S. sieve, impact forward at speed 2.",
            "In clean stainless steel Rapid Mixer Granulator, add in sequence:<br>I. 75.00kg of Sulfadoxine<br>II. 6.00kg of Maize Starch<br>III. 6.00kg of Microcrystalline Cellulose",
            "Dry blend at SLOW speed in Rapid Mixer Granulator for 10 minutes then at FAST speed for 5 minutes.",
        ],
        'wet_mixing_instructions': [
            "Boil 25.0 litres of purified Water in stainless steel vessel.",
            "Meanwhile, add in sequence in a clean stainless steel mixing vessel:<br>I. 8 litres of cold purified water<br>II. 184.5g of Methylparaben<br>III. 27.0g of Propylparaben",
            "Mix until smooth uniform slurry forms.",
            "Add hot boiling water to the slurry while vigorously stirring. A smooth uniform paste forms.",
            "Add the paste to the dry blend and mix at SLOW speed for 3 minutes then at FAST speed for 3 minutes.",
        ],
        'drying_instructions': [
            "Dry the granules at 70°C for 45 minutes in Fluid Bed Drier then remove and turn around the granules with a stainless steel scoop. Repeat the above procedure then mill the granules in Comminuting Mill fitted with sieve size 4. Redry the granules at 70°C for 45 minutes.",
            "Repeat the above procedure for the rest of the lots.",
        ],
        'final_drying_instructions': [
            "Let the granules cool to room temperature then sift through #14 on vibratory sifter then mill granules with Multimill fitted with 3mm sieve with knives forward at speed 2.",
        ],
    },
}


class Command(BaseCommand):
    help = 'Seed product fields and equipment entries for KAMADOL (13) and KAMSIDAR (11)'

    def handle(self, *args, **options):
        for product_id, fields in PRODUCTS.items():
            # Try by ID first; fall back to name search so it works on any server
            product = Product.objects.filter(id=product_id).first()
            if not product:
                name_hint = PRODUCT_NAME_MAP.get(product_id, '')
                product = Product.objects.filter(product_name__icontains=name_hint).first()
            if not product:
                self.stderr.write(self.style.ERROR(f'Product id={product_id} / name~"{PRODUCT_NAME_MAP.get(product_id)}" not found — skipping'))
                continue

            # ── Update product fields ──────────────────────────────────────────
            for field, value in fields.items():
                setattr(product, field, value)
            product.save()
            self.stdout.write(f'  Updated fields for {product.product_name} (id={product_id})')

            # ── Seed equipment entries ─────────────────────────────────────────
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
            self.stdout.write(f'  Created {created} equipment entries for {product.product_name}')

        self.stdout.write(self.style.SUCCESS('Done — tablet data seeded successfully.'))
