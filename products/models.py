from django.db import models
from workflow.constants import (
    PRODUCT_TYPE_CHOICES, COATING_TYPE_CHOICES, TABLET_TYPE_CHOICES,
    CAPSULE_TYPE_CHOICES,
    get_product_type_choices, get_coating_type_choices, get_tablet_type_choices
)

class Product(models.Model):
    """Product master data for pharmaceutical products"""
    
    # Use constants imported from workflow
    
    # Essential fields only
    product_name = models.CharField(max_length=200)
    product_code = models.CharField(
        max_length=50,
        blank=True,
        help_text="Product code for identification"
    )
    generic_name = models.CharField(
        max_length=300,
        blank=True,
        help_text="Generic pharmaceutical name (e.g., Paracetamol Tablets BP 500mg)"
    )
    
    # BMR Header Information
    bmr_revision_no = models.CharField(
        max_length=20,
        blank=True,
        help_text="BMR Revision Number (e.g., 03)"
    )
    mfr_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="Master Formula Record Number (e.g., KPI/MFR/003/00)"
    )
    reference_sop_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="Reference SOP Number (e.g., QAD/022/01)"
    )
    
    # Use base product type choices at model-level (keeps migrations stable and admin consistent)
    # The admin form dynamically augments choices from the DB via `get_product_type_choices()`.
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES)
    
    # Tablet specific fields (only show when product_type is 'tablet')
    coating_type = models.CharField(
        max_length=20,
        choices=COATING_TYPE_CHOICES,
        blank=True,
        help_text="Only applicable for tablets - whether the tablet is coated or not"
    )
    tablet_type = models.CharField(
        max_length=20, 
        choices=TABLET_TYPE_CHOICES,
        blank=True,
        help_text="Only applicable for tablets - normal or tablet type 2"
    )
    capsule_type = models.CharField(
        max_length=20,
        choices=CAPSULE_TYPE_CHOICES,
        blank=True,
        default='normal',
        help_text="Only applicable for capsules - normal (blister packing) or UG (bulk packing)"
    )
    
    # Batch size configuration - moved from BMR to Product
    standard_batch_size = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=1000,  # Default batch size
        help_text="Standard batch size for this product"
    )
    batch_size_unit = models.CharField(
        max_length=20,
        default='units',
        help_text="Unit of measurement for batch size (automatically set based on product type)"
    )
    
    # New packaging size field
    packaging_size_in_units = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Size of individual packaging unit (e.g., tablets per blister, capsules per bottle, ml per tube)"
    )
    
    # Pack Size Configurations (for BMR Header)
    pack_size_1_code = models.CharField(
        max_length=50,
        blank=True,
        help_text="Pack size 1 code (e.g., KMD1TB)"
    )
    pack_size_1_description = models.CharField(
        max_length=200,
        blank=True,
        help_text="Pack size 1 description (e.g., 10x10 Blisters)"
    )
    pack_size_2_code = models.CharField(
        max_length=50,
        blank=True,
        help_text="Pack size 2 code (e.g., KMD2TB)"
    )
    pack_size_2_description = models.CharField(
        max_length=200,
        blank=True,
        help_text="Pack size 2 description (e.g., 100 Blisters X 10 Tablets)"
    )
    pack_size_3_code = models.CharField(
        max_length=50,
        blank=True,
        help_text="Pack size 3 code (e.g., KMD3TJ)"
    )
    pack_size_3_description = models.CharField(
        max_length=200,
        blank=True,
        help_text="Pack size 3 description (e.g., 500's)"
    )
    pack_size_4_code = models.CharField(
        max_length=50,
        blank=True,
        help_text="Pack size 4 code (e.g., KMD4TJ)"
    )
    pack_size_4_description = models.CharField(
        max_length=200,
        blank=True,
        help_text="Pack size 4 description (e.g., 1000's)"
    )
    
    # ============================================================================
    # PRODUCT SPECIFICATIONS (Auto-fill BMR Forms)
    # ============================================================================
    
    # Label Claim & Product Details
    label_claim = models.TextField(
        blank=True,
        help_text="Complete label claim (e.g., Each Kamadol Tablet Contains: Paracetamol BP 500 mg)"
    )
    color_description = models.CharField(
        max_length=100,
        blank=True,
        help_text="Product color (e.g., White)"
    )
    shelf_life_years = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Shelf life in years (e.g., 3 years)"
    )
    storage_conditions = models.TextField(
        blank=True,
        help_text="Storage requirements (e.g., Store in a cool & dry place. Protect from direct light, heat and moisture.)"
    )
    mfg_license_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Manufacturing license number (e.g., NDA/MAL/HDP/1887)"
    )
    brand_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Brand/Trade name if different from product name"
    )
    market_type = models.CharField(
        max_length=50,
        blank=True,
        default='Domestic/Local',
        help_text="Target market (e.g., Domestic/Local, Export)"
    )
    
    # Tablet/Capsule Specifications (for compression & QC)
    average_weight_uncoated = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="Average weight in mg (e.g., 591.1mg for uncoated tablets)"
    )
    weight_tolerance_percentage = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        default=5.0,
        help_text="Weight tolerance ±% (default: ±5%)"
    )
    standard_weight_tolerance_percentage = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        default=2.0,
        help_text="Standard Weight tolerance ±% (default: ±2%)"
    )
    hardness_min = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Minimum hardness in kg/cm² (e.g., 4)"
    )
    hardness_max = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Maximum hardness in kg/cm² (e.g., 8)"
    )
    thickness_nominal = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Nominal thickness in mm (e.g., 4.35)"
    )
    thickness_tolerance = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        default=0.3,
        help_text="Thickness tolerance ± in mm (e.g., ±0.3)"
    )
    diameter_nominal = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Nominal diameter in mm (e.g., 12.5)"
    )
    diameter_tolerance = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        default=0.2,
        help_text="Diameter tolerance ± in mm (e.g., ±0.2)"
    )
    friability_max = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        default=1.0,
        help_text="Maximum friability % (e.g., NMT 1.0%)"
    )
    disintegration_time_max = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Maximum disintegration time in minutes (e.g., NMT 15 min)"
    )
    dissolution_spec = models.CharField(
        max_length=200,
        blank=True,
        help_text="Dissolution specification (e.g., Not Less than 70% for each Tablet)"
    )
    
    # Assay Specifications
    assay_min_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        default=95.0,
        help_text="Minimum assay percentage of label claim (e.g., 95.0%)"
    )
    assay_max_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        default=105.0,
        help_text="Maximum assay percentage of label claim (e.g., 105.0%)"
    )
    
    # Compression Specifications
    punch_size = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Punch size in mm (e.g., 12.5mm)"
    )
    punch_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="Punch type (e.g., D-TOOLING, B-TOOLING)"
    )
    upper_punch_description = models.CharField(
        max_length=200,
        blank=True,
        help_text="Upper punch description (e.g., Flat Beveled, Embossed P500 over B/L and KPI under B/L)"
    )
    lower_punch_description = models.CharField(
        max_length=200,
        blank=True,
        help_text="Lower punch description (e.g., Flat Beveled, Plain)"
    )
    # UG/Export Market Variations
    punch_size_ug = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Punch size for UG market in mm (if different)"
    )
    punch_shape_trade = models.CharField(
        max_length=100,
        blank=True,
        help_text="Punch shape for Trade (e.g. Round flat)"
    )
    punch_shape_ug = models.CharField(
        max_length=100,
        blank=True,
        help_text="Punch shape for UG (e.g. Round flat)"
    )
    upper_punch_description_ug = models.CharField(
        max_length=200,
        blank=True,
        help_text="Upper punch description for UG market"
    )
    lower_punch_description_ug = models.CharField(
        max_length=200,
        blank=True,
        help_text="Lower punch description for UG market"
    )

    tablet_appearance_trade = models.TextField(
        blank=True,
        help_text="Tablet appearance for Trade market (e.g., White round flat tablets embossed 'P500' above and 'KPI' below)"
    )
    tablet_appearance_ug = models.TextField(
        blank=True,
        help_text="Tablet appearance for UG market if different"
    )
    
    # Granulation Specifications
    lod_min_percentage = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        default=1.60,
        help_text="Minimum Loss on Drying % (e.g., 1.60%)"
    )
    lod_max_percentage = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        default=3.60,
        help_text="Maximum Loss on Drying % (e.g., 3.60%)"
    )
    drying_temperature = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Standard drying temperature in °C (e.g., 70°C)"
    )
    drying_time_minutes = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Standard drying time in minutes (e.g., 45 min)"
    )
    dry_mixing_slow_time = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        default=10.0,
        help_text="Dry mixing slow speed time in minutes (e.g., 10 min)"
    )
    dry_mixing_fast_time = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        default=5.0,
        help_text="Dry mixing fast speed time in minutes (e.g., 5 min)"
    )
    wet_mixing_slow_time = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        default=3.0,
        help_text="Wet mixing slow speed time in minutes (e.g., 3 min)"
    )
    wet_mixing_fast_time = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        default=3.0,
        help_text="Wet mixing fast speed time in minutes (e.g., 3 min)"
    )
    milling_sieve_size = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Milling sieve size in mm (e.g., 4mm)"
    )
    
    # Blending Specifications
    blending_time_minutes = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        default=20.0,
        help_text="Blending time in minutes (e.g., 20 min)"
    )
    magnesium_stearate_sieve_mesh = models.IntegerField(
        null=True,
        blank=True,
        default=40,
        help_text="Mesh size for Magnesium Stearate sifting (e.g., #40)"
    )
    
    # Environmental Specifications
    max_temperature_celsius = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        default=28.0,
        help_text="Maximum manufacturing temperature in °C (e.g., NMT 28°C)"
    )
    min_humidity_percentage = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        default=40.0,
        help_text="Minimum relative humidity % (e.g., 40%)"
    )
    max_humidity_percentage = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        default=65.0,
        help_text="Maximum relative humidity % (e.g., 65%)"
    )
    
    # Yield Specifications
    min_yield_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        default=98.00,
        help_text="Minimum acceptable yield % (e.g., 98%)"
    )
    max_yield_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        default=102.00,
        help_text="Maximum acceptable yield % (e.g., 102%)"
    )
    
    # Product-specific instructions
    special_instructions = models.TextField(
        blank=True,
        help_text="Any special manufacturing instructions specific to this product"
    )

    # Page 7 Content - Dynamic Content
    general_instructions = models.JSONField(
        default=list, 
        blank=True, 
        help_text="List of strings for General Instructions (Page 7)"
    )
    safety_precautions = models.JSONField(
        default=list, 
        blank=True,
        help_text="List of strings for Safety Precautions (Page 7)"
    )
    general_sops = models.JSONField(
        default=list,
        blank=True,
        help_text="List of dictionaries {'sn': '1', 'title': '...', 'sop_no': '...'} for General SOPs (Page 7)"
    )

    # Page 8 Content - Dynamic Content
    dispensing_clearance_start_items = models.JSONField(
        default=list,
        blank=True,
        help_text="List of strings for Dispensing Line Clearance Beginning Activities (Page 8)"
    )
    dispensing_clearance_end_items = models.JSONField(
        default=list,
        blank=True,
        help_text="List of strings for Dispensing Line Clearance Ending Activities (Page 8)"
    )

    # Page 9 Content - Granulation/Mixing
    granulation_steps = models.JSONField(
        default=list,
        blank=True,
        help_text="List of strings for Granulation/Mixing Process Steps (Page 9)"
    )
    
    # Page 10 Content - Granulation Line Clearance
    granulation_clearance_start_items = models.JSONField(
        default=list,
        blank=True,
        help_text="List of strings for Granulation Line Clearance Beginning Activities (Page 10)"
    )
    granulation_clearance_end_items = models.JSONField(
        default=list,
        blank=True,
        help_text="List of strings for Granulation Line Clearance Ending Activities (Page 10)"
    )

    # Page 16 Content - Blending Line Clearance
    blending_clearance_start_items = models.JSONField(
        default=list,
        blank=True,
        help_text="List of strings for Blending Line Clearance Beginning Activities (Page 16)"
    )
    blending_clearance_end_items = models.JSONField(
        default=list,
        blank=True,
        help_text="List of strings for Blending Line Clearance Ending Activities (Page 16)"
    )

    # Page 20 Content - Compression Line Clearance
    compression_clearance_start_items = models.JSONField(
        default=list,
        blank=True,
        help_text="List of strings for Compression Line Clearance Beginning Activities (Page 20)"
    )
    compression_clearance_end_items = models.JSONField(
        default=list,
        blank=True,
        help_text="List of strings for Compression Line Clearance Ending Activities (Page 20)"
    )

    # Page 38 Content - Sorting Line Clearance
    sorting_clearance_start_items = models.JSONField(
        default=list,
        blank=True,
        help_text="List of strings for Sorting/Inspection Line Clearance Beginning Activities (Page 38)"
    )
    sorting_clearance_end_items = models.JSONField(
        default=list,
        blank=True,
        help_text="List of strings for Sorting/Inspection Line Clearance Ending Activities (Page 38)"
    )

    # Page 42 Content - Packaging Line Clearance
    packing_clearance_start_items = models.JSONField(
        default=list,
        blank=True,
        help_text="List of strings for Packaging Line Clearance Beginning Activities (Page 42)"
    )
    packing_clearance_end_items = models.JSONField(
        default=list,
        blank=True,
        help_text="List of strings for Packaging Line Clearance Ending Activities (Page 42)"
    )

    # Page 11 Content - Detailed Granulation
    granulation_lot_count = models.PositiveIntegerField(
        default=4, 
        help_text="Number of lots for granulation (Page 11)"
    )
    dry_mixing_instructions = models.JSONField(
        default=list, 
        blank=True, 
        help_text="List of strings for Dry Mixing instructions (Page 11)"
    )
    wet_mixing_instructions = models.JSONField(
        default=list, 
        blank=True,
        help_text="List of strings for Wet Mixing instructions (Page 11)"
    )

    # Page 12 Content - Drying
    drying_instructions = models.JSONField(
        default=list,
        blank=True,
        help_text="List of strings for Drying instructions (Page 12)"
    )

    # Page 13 Content - Final Drying & QA
    final_drying_instructions = models.JSONField(
        default=list,
        blank=True,
        help_text="List of strings for Final Drying instructions (Page 13)"
    )
    lod_limits = models.CharField(
        max_length=100,
        default="1.60-3.60",
        help_text="LOD Limits in % (e.g. 1.60-3.60)"
    )
    
    # Page 14 Content - Yield
    yield_drum_count = models.PositiveIntegerField(
        default=10,
        help_text="Number of rows for Yield/Drum table (Page 14)"
    )

    # Page 15 Content - Yield Reconciliation
    yield_limit_min = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=98.00,
        help_text="Minimum permissible yield % (Default: 98.00)"
    )
    yield_limit_max = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=102.00,
        help_text="Maximum permissible yield % (Default: 102.00)"
    )

    # Page 16 Content - Blending/Lubrication
    magnesium_stearate_qty = models.CharField(
        max_length=50,
        default="256gm",
        help_text="Quantity of Magnesium Stearate (e.g. 256gm)"
    )
    sieve_size_lubrication = models.CharField(
        max_length=50, 
        default="#40",
        help_text="Mesh size for Lubrication (e.g. #40)"
    )
    blending_time = models.CharField(
        max_length=50,
        default="20 minutes",
        help_text="Blending/Mixing time (e.g. 20 minutes)"
    )
    
    # Page 23 Content - Compression Instructions
    compression_instructions = models.JSONField(
        default=list,
        blank=True,
        help_text="List of strings for Compression Setting Instructions (Page 23)"
    )

    # Compression Environment Limits
    compression_temperature_limit = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        default=28.0,
        help_text="Maximum temperature for compression area in °C (e.g. 28.0)"
    )
    compression_rh_limit_min = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        default=40.0,
        help_text="Minimum relative humidity for compression area in % (e.g. 40.0)"
    )
    compression_rh_limit_max = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        default=65.0,
        help_text="Maximum relative humidity for compression area in % (e.g. 65.0)"
    )

    # =============================================
    # FILM COATING-SPECIFIC FIELDS
    # =============================================

    average_weight_coated = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="Average weight of coated tablets in mg (e.g., 556.81mg for FORMIN)"
    )
    coating_hardness_min = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Post-coating minimum hardness kg/cm² (e.g., 4 for NLT 4 kg/cm²)"
    )
    coating_disintegration_max = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Post-coating maximum disintegration time in minutes (e.g., 30)"
    )
    coating_lot_count = models.PositiveIntegerField(
        default=4,
        help_text="Number of coating lots (e.g., 4 for FORMIN)"
    )
    coating_pan_speed = models.CharField(
        max_length=50,
        blank=True,
        help_text="Coating pan speed e.g. 10-14 RPM"
    )
    coating_hot_air_temp = models.CharField(
        max_length=50,
        blank=True,
        help_text="Coating hot air temperature e.g. 80 ± 5°C"
    )
    coating_tablet_bed_temp = models.CharField(
        max_length=50,
        blank=True,
        help_text="Coating tablet bed temperature e.g. 40 ± 5°C"
    )
    coating_spray_pressure = models.CharField(
        max_length=50,
        blank=True,
        help_text="Coating spray gun pressure e.g. 2.0-2.25 kg/cm³"
    )
    coating_storage_pressure = models.CharField(
        max_length=50,
        blank=True,
        help_text="Coating storage tank pressure e.g. 0.5-1.0 kg/cm³"
    )
    coating_solution_instructions = models.JSONField(
        default=list,
        blank=True,
        help_text="List of strings for coating solution preparation steps"
    )
    coating_clearance_start_items = models.JSONField(
        default=list,
        blank=True,
        help_text="List of strings for Film Coating Line Clearance Beginning Activities"
    )
    coating_clearance_end_items = models.JSONField(
        default=list,
        blank=True,
        help_text="List of strings for Film Coating Line Clearance Ending Activities"
    )
    coating_precautions = models.JSONField(
        default=list,
        blank=True,
        help_text='List of precaution strings shown on the coating page, e.g. ["Once started the film coating process should not be interrupted.", ...]'
    )
    coating_procedure_steps = models.JSONField(
        default=list,
        blank=True,
        help_text='List of procedure step strings for the coating procedure section, e.g. ["Load the tablets into the pan...", ...]'
    )
    coating_equipment_params = models.JSONField(
        default=list,
        blank=True,
        help_text='List of dicts for equipment settings table rows: [{"name": "Spray gun pressure", "set_value": "2.0–2.25 kg/cm³"}, ...]'
    )
    blending_without_mag_time = models.CharField(
        max_length=50,
        blank=True,
        help_text="Blend time without Magnesium Stearate e.g. 15 minutes (coated tablets)"
    )
    lubrication_with_mag_time = models.CharField(
        max_length=50,
        blank=True,
        help_text="Lubrication time with Magnesium Stearate e.g. 5 minutes (coated tablets)"
    )

    # =============================================
    # OINTMENT-SPECIFIC FIELDS
    # =============================================

    # Mixing Line Clearance
    mixing_clearance_start_items = models.JSONField(
        default=list,
        blank=True,
        help_text="List of strings for Mixing Line Clearance Beginning Activities"
    )
    mixing_clearance_end_items = models.JSONField(
        default=list,
        blank=True,
        help_text="List of strings for Mixing Line Clearance Ending Activities"
    )

    # Mixing Process
    mixing_steps = models.JSONField(
        default=list,
        blank=True,
        help_text="List of dicts for mixing process steps e.g. [{'step': 1, 'instruction': '...'}]"
    )
    mixing_equipment = models.JSONField(
        default=list,
        blank=True,
        help_text="List of dicts [{'name': 'Planetary Mixer', 'id': 'ON-01'}] for mixing equipment"
    )
    mixing_jacket_temperature = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True, default=70.0,
        help_text="Jacket temperature for mixing in °C (e.g. 70.0)"
    )
    mixing_cool_temperature = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True, default=40.0,
        help_text="Cool-down temperature before QA sample in °C (e.g. 40.0)"
    )
    mixing_appearance = models.CharField(
        max_length=100, blank=True, default="White Smooth Cream",
        help_text="Expected appearance of cream after mixing"
    )

    # Tube Filling Line Clearance
    tube_filling_clearance_start_items = models.JSONField(
        default=list,
        blank=True,
        help_text="List of strings for Tube Filling Line Clearance Beginning Activities"
    )
    tube_filling_clearance_end_items = models.JSONField(
        default=list,
        blank=True,
        help_text="List of strings for Tube Filling Line Clearance Ending Activities"
    )

    # Tube Filling Specs
    tube_filling_weight = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True, default=15.00,
        help_text="Net content per tube in grams (e.g. 15.00)"
    )
    tube_filling_equipment = models.JSONField(
        default=list,
        blank=True,
        help_text="List of dicts [{'name': 'Tube Filling Machine', 'id': 'ON-03'}]"
    )
    tube_filling_yield_min = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True, default=99.00,
        help_text="Minimum permissible yield % for tube filling (e.g. 99.00)"
    )
    tube_filling_yield_max = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True, default=101.00,
        help_text="Maximum permissible yield % for tube filling (e.g. 101.00)"
    )
    tube_filling_hopper_temperature = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True, default=40.0,
        help_text="Hopper temperature during tube filling in °C (e.g. 40.0)"
    )
    tube_filling_ipc_page_count = models.PositiveIntegerField(
        default=3,
        help_text="Number of production IPC report pages for tube filling"
    )
    tube_filling_qa_ipc_page_count = models.PositiveIntegerField(
        default=2,
        help_text="Number of QA IPC report pages for tube filling"
    )

    # Packaging (Ointment)
    secondary_packaging_clearance_start_items = models.JSONField(
        default=list,
        blank=True,
        help_text="List of strings for Secondary Packaging Line Clearance Beginning Activities"
    )
    secondary_packaging_clearance_end_items = models.JSONField(
        default=list,
        blank=True,
        help_text="List of strings for Secondary Packaging Line Clearance Ending Activities"
    )
    packing_instructions = models.JSONField(
        default=list,
        blank=True,
        help_text="List of strings for packing process instructions"
    )
    packing_reference_docs = models.JSONField(
        default=list,
        blank=True,
        help_text="List of reference document names for packing"
    )
    secondary_packing_steps = models.JSONField(
        default=list,
        blank=True,
        help_text="List of strings for secondary packing procedure steps"
    )

    # =============================================
    # CAPSULE-SPECIFIC FIELDS
    # =============================================
    capsule_size = models.CharField(
        max_length=10, blank=True, default='#1',
        help_text="Capsule shell size (e.g., #1)"
    )
    capsule_body_colour_trade = models.CharField(
        max_length=150, blank=True,
        help_text="Capsule body colour for Trade (e.g., Peach)"
    )
    capsule_cap_colour_trade = models.CharField(
        max_length=150, blank=True,
        help_text="Capsule cap colour for Trade (e.g., Maroon)"
    )
    capsule_body_print_trade = models.CharField(
        max_length=150, blank=True,
        help_text="Capsule body printing for Trade (e.g., KAM AMOXY 250)"
    )
    capsule_cap_print_trade = models.CharField(
        max_length=150, blank=True,
        help_text="Capsule cap printing for Trade (e.g., KPI)"
    )
    capsule_body_colour_ug = models.CharField(
        max_length=150, blank=True,
        help_text="Capsule body colour for UG market (e.g., Peach)"
    )
    capsule_cap_colour_ug = models.CharField(
        max_length=150, blank=True,
        help_text="Capsule cap colour for UG market (e.g., Maroon)"
    )
    capsule_body_print_ug = models.CharField(
        max_length=150, blank=True,
        help_text="Capsule body printing for UG market (e.g., KAM AMOXY 250)"
    )
    capsule_cap_print_ug = models.CharField(
        max_length=150, blank=True,
        help_text="Capsule cap printing for UG market (e.g., UG & KPI LOGO)"
    )
    avg_empty_shell_weight_mg = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        help_text="Average weight of empty capsule shells in mg (e.g., 91.00)"
    )
    capsule_appearance = models.CharField(
        max_length=300, blank=True,
        help_text="Capsule appearance spec for IPQC table (e.g., Maroon cap printed 'KPI logo', Peach body printed 'KAM AMOXY 250')"
    )
    fill_weight_mg = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        help_text="Standard fill weight per capsule in mg (e.g., 320.00)"
    )
    capsule_machine_speed_min = models.DecimalField(
        max_digits=5, decimal_places=1, null=True, blank=True, default=15.0,
        help_text="Minimum capsule filling machine speed in RPM (e.g., 15)"
    )
    capsule_machine_speed_max = models.DecimalField(
        max_digits=5, decimal_places=1, null=True, blank=True, default=40.0,
        help_text="Maximum capsule filling machine speed in RPM (e.g., 40)"
    )
    lock_length_min = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
        help_text="Capsule lock length minimum in mm (e.g., 18.90)"
    )
    lock_length_max = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
        help_text="Capsule lock length maximum in mm (e.g., 19.90)"
    )
    theoretical_weight_kg = models.DecimalField(
        max_digits=10, decimal_places=3, null=True, blank=True,
        help_text="Theoretical batch weight in kg (e.g., 160.000)"
    )

    # System fields
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def is_coated(self):
        """Backward compatibility property"""
        return self.coating_type == 'coated'

    def __init__(self, *args, **kwargs):
        # Accept legacy kwarg(s) when creating Product instances in tests
        # Some older tests or fixtures may pass fields that are no longer model fields
        # (e.g., `is_coated`, `strength`). Pop and handle what we can, ignore others.
        is_coated = kwargs.pop('is_coated', None)
        legacy_strength = kwargs.pop('strength', None)

        super().__init__(*args, **kwargs)

        if is_coated is not None:
            # Normalize into coating_type for storage
            self.coating_type = 'coated' if is_coated else 'uncoated'

        # Keep legacy_strength as an attribute for test objects if provided
        if legacy_strength is not None:
            try:
                setattr(self, 'strength', legacy_strength)
            except Exception:
                pass
    
    def __str__(self):
        if self.product_type == 'tablet':
            coating_status = self.get_coating_type_display() if self.coating_type else "Uncoated"
            tablet_display = self.get_tablet_type_display() if self.tablet_type else "Normal"
            return f"{self.product_name} ({tablet_display}, {coating_status})"
        return f"{self.product_name} ({self.get_product_type_display()})"
    
    def save(self, *args, **kwargs):
        from workflow.constants import is_tablet, is_capsule, is_ointment, PRODUCT_TYPES
        
        # Clear tablet-specific fields if product is not a tablet
        if self.product_type != PRODUCT_TYPES['TABLET']:
            self.coating_type = ''
            self.tablet_type = ''
        
        # Set batch_size_unit based on product type
        if is_tablet(self.product_type):
            self.batch_size_unit = 'tablets'
        elif is_capsule(self.product_type):
            self.batch_size_unit = 'capsules'
        elif is_ointment(self.product_type):
            self.batch_size_unit = 'tubes'
        else:
            self.batch_size_unit = 'units'  # Default fallback
            
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['product_name']

class ProductIngredient(models.Model):
    """Active and inactive ingredients for each product"""
    
    INGREDIENT_TYPE_CHOICES = [
        ('active', 'Active Ingredient'),
        ('inactive', 'Inactive Ingredient'),
        ('excipient', 'Excipient'),
        ('coating', 'Coating Material'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='ingredients')
    order = models.PositiveIntegerField(default=0, help_text="Display order (1=first row)")
    ingredient_name = models.CharField(max_length=200, help_text="Full description e.g. 'Miconazole Nitrate BP'")
    item_code = models.CharField(max_length=50, blank=True, help_text="Material code e.g. MCZ1NN (shown under description)")
    ingredient_type = models.CharField(max_length=20, choices=INGREDIENT_TYPE_CHOICES)
    quantity_per_unit = models.DecimalField(max_digits=10, decimal_places=4, help_text="Unit quantity in mg/g")
    overage = models.DecimalField(max_digits=10, decimal_places=4, default=0, help_text="Overage in mg/g (usually 0)")
    lot_count = models.PositiveIntegerField(default=1, help_text="Number of lots this ingredient is dispensed in (e.g. 1 or 4)")
    unit_of_measure = models.CharField(max_length=20, default='mg/g', help_text="Unit e.g. mg/g, g, ml")
    supplier = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        code = f" [{self.item_code}]" if self.item_code else ""
        return f"{self.product.product_name} - {self.ingredient_name}{code}"

class ProductSpecification(models.Model):
    """Product specifications and quality parameters"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='specifications')
    parameter_name = models.CharField(max_length=100)
    specification = models.CharField(max_length=200)
    test_method = models.CharField(max_length=200)
    acceptance_criteria = models.CharField(max_length=200)
    
    def __str__(self):
        return f"{self.product.product_name} - {self.parameter_name}"


class PackagingMaterial(models.Model):
    """Packaging materials required for a product — used in the Packaging Materials Requisition Sheet"""

    PACK_TYPE_CHOICES = [
        ('blister', 'Blister Pack'),
        ('bulk', 'Bulk Pack'),
        ('both', 'Both / All Pack Types'),
    ]
    UNIT_CHOICES = [
        ('Kg', 'Kg'),
        ('PCS', 'PCS'),
        ('Roll', 'Roll'),
        ('Box', 'Box'),
        ('Litre', 'Litre'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='packaging_materials')
    item_code = models.CharField(max_length=50, help_text="Item code e.g. KMD 203TB")
    item_description = models.CharField(max_length=200, help_text="Full item description")
    units = models.CharField(max_length=20, choices=UNIT_CHOICES, default='PCS')
    pack_type = models.CharField(
        max_length=10, choices=PACK_TYPE_CHOICES, default='blister',
        help_text="Which pack size section this item belongs to"
    )
    order = models.PositiveIntegerField(default=0, help_text="Display order within pack type group")

    class Meta:
        ordering = ['pack_type', 'order', 'item_code']

    def __str__(self):
        return f"{self.product.product_name} — {self.item_code} ({self.get_pack_type_display()})"


class ProductRevisionHistory(models.Model):
    """BMR revision history entries for a product — editable from the Django admin."""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='revision_history',
    )
    revision_no = models.CharField(
        max_length=10,
        help_text="Revision number, e.g. 01, 02, 03",
    )
    changes_incorporated = models.TextField(
        help_text="Full text of changes incorporated in this revision",
    )
    reason_of_change = models.TextField(
        blank=True,
        help_text="Reason / justification for the change",
    )
    effective_date = models.CharField(
        max_length=50,
        blank=True,
        help_text="Effective date (leave blank if not yet assigned)",
    )
    order = models.PositiveSmallIntegerField(
        default=0,
        help_text="Display order (lower = earlier; use 1, 2, 3 …)",
    )

    class Meta:
        ordering = ['order', 'revision_no']
        verbose_name = 'BMR Revision History'
        verbose_name_plural = 'BMR Revision History'

    def __str__(self):
        return f"{self.product.product_name} — Rev {self.revision_no}"
