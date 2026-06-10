"""
Phase-specific Line Clearance items for each manufacturing phase.
Each phase has DIFFERENT beginning and ending items specific to the equipment 
and procedures used in that phase. Some phases have NO line clearance at all.

Usage in views:
    from workflow.line_clearance_items import get_lc_items
    beginning_items, ending_items = get_lc_items('granulation')
"""


# ============================================================
# DISPENSING LINE CLEARANCE (BMR Page 8)
# ============================================================
DISPENSING_LC_BEGINNING = [
    "Area cleaning is done as per SOP.",
    "Ensure the absence of batch documents, labels, materials or remnants of previous product or batch.",
    "Ensure availability of the BMR for the in-coming batch and Verify that ALL materials and facilities for new batch are available, labeled and identified.",
    "Gowning and de-gowning procedure is followed.",
    "Dispensing Room, Dispensing booth, Balances and dispensing tools are clean and have status as ready for use.",
    "Clean scoops, containers and poly bags are available for dispensing as per SOP.",
    "Manometer reading of dispensing booth RLAF is within the required limit.\nActual Manometer reading: __________",
    "Balance Calibration carried out before starting dispensing.",
    "Verify the release status & retest validity period of each material.",
    "Ensure Environmental conditions are met as per SOP.\nTemperature NMT 28 °C __________\nRelative Humidity (40-65)% __________",
    "Ensure that the RLAF is started 15 minutes before start of the dispensing activities.",
]

DISPENSING_LC_ENDING = [
    "All material from current product have been removed.",
    "All facilities have been cleaned and labeled.",
    "The area has been cleaned and labeled.",
    "All paperwork for the current batch has been completed.",
    "Reconciliation of current batch has been done.",
    "Ensure that utensils and accessories from previous operations have been removed.",
]

# Special fields for dispensing (environmental readings)
DISPENSING_LC_SPECIAL_FIELDS = {
    'has_environmental': True,
    'environmental_item_index': 8,  # Item 8 has temperature/humidity inputs
}


# ============================================================
# GRANULATION LINE CLEARANCE (BMR Page 10)
# ============================================================
GRANULATION_LC_BEGINNING = [
    "Area cleaning as per SOP.",
    "Ensure that all the previous product containers, material, and labels are removed from the manufacturing area.",
    "Gowning procedure is followed.",
    "Ensure that status board is displayed mentioning Product Name, Batch No, B. Size, Mfg. Date, Exp.Date & Status with sign & date.",
    "Check the proper cleanliness of Vibro-sifter, Paste Kettle, RMG, FBD, Multi mill etc.",
    "Ensure that the Vibrosifter sieves, Multimill screen, FBD bags, Scoops etc. cleaned.",
    "Check and ensure that Balance Calibration & Verification records are updated.",
    "Ensure Environmental conditions are met as per SOP.\nTemperature NMT 28 °C __________\nRelative Humidity (40-65)% __________",
    "Check the Integrity/Intactness of FBD gaskets, Product Bowl sieves and Dutch Meshes/Distribution Plates, and the sifting and milling sieves.",
]

GRANULATION_LC_ENDING = [
    "All material from current product have been removed.",
    "Check the cleanliness of Air grills/light fixtures and waste bins.",
    "The area has been cleaned and labeled.",
    "All paperwork for the current batch has been completed.",
    "Reconciliation of current batch has been done.",
    "Machine cleanliness has been checked and labeled.",
]

GRANULATION_LC_SPECIAL_FIELDS = {
    'has_environmental': True,
    'environmental_item_index': 8,
}


# ============================================================
# BLENDING/LUBRICATION LINE CLEARANCE (BMR Page 16)
# NOTE: Different table format - 2-column items with S/N
# ============================================================
BLENDING_LC_BEGINNING = [
    "Area cleaning as per SOP.",
    "Ensure that all the previous product containers, materials and labels are removed from the manufacturing area.",
    "Gowning procedure is followed.",
    "Ensure that status board is displayed mentioning Product Name, Batch No, B. Size, Mfg. Date, Exp.Date & Status with sign & date.",
    "Check the proper cleanliness of the Air Supply and Return grills and Air Conditioning System.",
    "Ensure that Vibrosifter sieves/Double Cone Blender/Scoops etc. are cleaned.",
    "Ensure Environmental conditions are met as per SOP.\nTemperature NMT 28 °C __________\nRelative Humidity (40 to 65%) __________",
    "Ensure that the balance used for weighing has been calibrated and within the qualification period.",
]

BLENDING_LC_ENDING = [
    "All material from current product have been removed.",
    "Check the cleanliness of Air grills/light fixtures and waste bins.",
    "The area has been cleaned and labeled.",
    "All paperwork for the current batch has been completed.",
    "Reconciliation of current batch has been done.",
    "Machine cleanliness has been checked and labeled.",
]

BLENDING_LC_SPECIAL_FIELDS = {
    'has_environmental': True,
    'environmental_item_index': 7,
}


# ============================================================
# COMPRESSION LINE CLEARANCE (BMR Page 20)
# ============================================================
COMPRESSION_LC_BEGINNING = [
    "Area cleaning as per SOP.",
    "Ensure that all the previous product containers, materials and labels are removed from the manufacturing area.",
    "Gowning procedure is followed.",
    "Ensure that status board is displayed mentioning Product Name, Batch No, B. Size, Mfg. Date, Exp.Date & Status with sign & date.",
    "Ensure the cleanliness of Compression Machine/Dies and Punches/Metal Detector/Deduster.",
    "Check the proper cleanliness of the Air Supply and Return grills and Air Conditioning System.",
    "Ensure Environmental conditions are met as per SOP.\nTemperature NMT 28 °C __________\nRelative Humidity (40 to 65%) __________",
    "Ensure that the balance used for weighing has been calibrated and within the qualification period.",
]

COMPRESSION_LC_ENDING = [
    "All material from current product have been removed.",
    "Check the cleanliness of Air grills/light fixtures and waste bins.",
    "The area has been cleaned and labeled.",
    "All paperwork for the current batch has been completed.",
    "Reconciliation of current batch has been done.",
    "Machine cleanliness has been checked and labeled.",
]

COMPRESSION_LC_SPECIAL_FIELDS = {
    'has_environmental': True,
    'environmental_item_index': 7,
}


# ============================================================
# TABLET INSPECTION & SORTING LINE CLEARANCE (BMR Page 38)
# NOTE: Combined QA+Status column format
# ============================================================
SORTING_LC_BEGINNING = [
    "Area cleaning as per SOP.",
    "Ensure that all the previous product containers, materials and labels are removed from the manufacturing area.",
    "Gowning procedure is followed.",
    "Ensure that status board is displayed mentioning Product Name, Batch No, B. Size, Mfg. Date, Exp.Date & Status with sign & date.",
    "Check the proper cleanliness of the Air Supply and Return grills and Air Conditioning System.",
    "Ensure that Vibrosifter sieves/Metal Detector/Deduster, Scoops etc. are cleaned.",
    "Ensure Environmental conditions are met as per SOP.\nTemperature NMT 28 °C __________\nRelative Humidity (40 to 65%) __________",
    "Ensure that the balance used for weighing has been calibrated and within the qualification period.",
]

SORTING_LC_ENDING = [
    "All material from current product have been removed.",
    "Check the cleanliness of Air grills/light fixtures and waste bins.",
    "The area has been cleaned and labeled.",
    "All paperwork for the current batch has been completed.",
    "Reconciliation of current batch has been done.",
    "Machine cleanliness has been checked and labeled.",
]

SORTING_LC_SPECIAL_FIELDS = {
    'has_environmental': True,
    'environmental_item_index': 7,
}


# ============================================================
# PACKAGING (PRIMARY) LINE CLEARANCE (BMR Page 42)
# NOTE: 9 beginning items (2 unique to packaging), unique ending item 6
# ============================================================
PACKAGING_LC_BEGINNING = [
    "Area cleaning as per SOP.",
    "Ensure that all the previous product containers, materials and labels are removed from the manufacturing area.",
    "Gowning procedure is followed.",
    "Ensure that status board is displayed mentioning Product Name, Batch No, B. Size, Mfg. Date, Exp.Date & Status with sign & date.",
    "Check the proper cleanliness of the Air Supply and Return grills and Air Conditioning System.",
    "Ensure that the Vibrosifter sieves, Metal Detector, Deduster, Scoops etc. are cleaned.",
    "Remove all the cartons, labels, strips, any material left over on the line and on the lower space of the conveyor belts.",
    "Put an authorized overprinted specimen of strip/blister/cartons/Label/Tube in the BMR for ready reference.",
    "Ensure Environmental conditions are met as per SOP.\nTemperature NMT 28 °C __________\nRelative Humidity (40 to 65%) __________",
]

PACKAGING_LC_ENDING = [
    "All material from current product have been removed.",
    "All facilities have been cleaned and labeled.",
    "The area has been cleaned and labeled.",
    "All paperwork for the current batch has been completed.",
    "Reconciliation of current batch has been done.",
    "Stereos of previous product are submitted to production Supervisor.",
]

PACKAGING_LC_SPECIAL_FIELDS = {
    'has_environmental': True,
    'environmental_item_index': 9,
}


# ============================================================
# SECONDARY PACKAGING LINE CLEARANCE (BMR Page 50)
# Similar to primary packaging but with different numbering
# ============================================================
SECONDARY_PACKAGING_LC_BEGINNING = [
    "Area cleaning as per SOP.",
    "Ensure that all the previous product containers, materials, and labels are removed from the manufacturing area.",
    "Gowning procedure is followed.",
    "Ensure that status board is displayed mentioning Product Name, Batch No, B. Size, Mfg. Date, Exp.Date & Status with sign & date.",
    "Check the proper cleanliness of the Air Supply and Return grills and Air Conditioning System.",
    "Ensure that the Vibrosifter sieves, Metal Detector, Deduster, Scoops etc. are cleaned.",
    "Remove all the cartons, labels, strips, any material left over on the line and on the lower space of the conveyor belts.",
    "Put an authorized overprinted specimen of strip/blister/cartons/Label/Tube in the BMR for ready reference.",
    "Ensure Environmental conditions are met as per SOP.\nTemperature NMT 28 °C __________\nRelative Humidity (40 to 65%) __________",
]

SECONDARY_PACKAGING_LC_ENDING = [
    "All material from current product have been removed.",
    "All facilities have been cleaned and labeled.",
    "The area has been cleaned and labeled.",
    "All paperwork for the current batch has been completed.",
    "Reconciliation of current batch has been done.",
    "Stereos of previous product are submitted to production Supervisor.",
]

SECONDARY_PACKAGING_LC_SPECIAL_FIELDS = {
    'has_environmental': True,
    'environmental_item_index': 9,
}


# ============================================================
# MIXING LINE CLEARANCE (Ointment BMR Page 8)
# ============================================================
MIXING_LC_BEGINNING = [
    "Area cleaning as per SOP.",
    "Check out all the previous product containers, material, labels are removed from the manufacturing area.",
    "Gowning procedure is followed.",
    "Ensure that status board is displayed with mentioning Product Name, Batch No, B. Size, Mfg. Date, Exp.Date & Status with sign & date.",
    "Check the proper cleanliness of the Air Supply and Return grills.",
    "Ensure that the Planetary Mixer and Mixing Utensils are cleaned.",
    "Check and ensure that Balance Calibration & Verification records are updated.",
    "Ensure Environmental conditions are met as per SOP.\nTemperature 20 °C - 26 °C __________\nRelative Humidity (50% - 60%) __________",
]

MIXING_LC_ENDING = [
    "All material from current product have been removed.",
    "All facilities have been cleaned and labeled.",
    "The area has been cleaned and labeled.",
    "All paperwork for the current batch has been completed.",
    "Reconciliation of current batch has been done.",
    "Machine(s) has been checked for cleanliness.",
]

MIXING_LC_SPECIAL_FIELDS = {
    'has_environmental': True,
    'environmental_item_index': 8,
}


# ============================================================
# CAPSULE FILLING LINE CLEARANCE (Capsule BMR Page 13)
# ============================================================
CAPSULE_FILLING_LC_BEGINNING = [
    "Area cleaning as per SOP.",
    "Ensure that all the previous product containers, material, and labels are removed from the manufacturing area.",
    "Gowning procedure is followed.",
    "Ensure that status board is displayed with mentioning Product Name, Batch No, B. Size, Mfg. Date, Exp.Date & Status with sign & date.",
    "Ensure the absence of batch documents, labels, materials or remnants of previous product or batch on each critical part.",
    "Are the following parts of the capsule filling machine cleaned: Hopper/Feeder/Turret/Below the turret, Y-chute/Powder collection.",
    "Check and ensure that Balance Calibration & Verification records are updated.",
    "Ensure Environmental conditions are met as per SOP. Temperature NMT 28\u00b0C ___ Relative Humidity (40-65)% ___",
]

CAPSULE_FILLING_LC_ENDING = [
    "All material from current product have been removed.",
    "All facilities have been cleaned and labeled.",
    "The area has been cleaned and labeled.",
    "All paperwork for the current batch has been completed.",
    "Reconciliation of current batch has been done.",
    "Machine(s) has been checked for cleanliness.",
]

CAPSULE_FILLING_LC_SPECIAL_FIELDS = {
    'has_environmental': True,
    'environmental_item_index': 8,
}


# ============================================================
# TUBE FILLING LINE CLEARANCE (Ointment BMR Page 11)
# ============================================================
TUBE_FILLING_LC_BEGINNING = [
    "Area cleaning as per SOP.",
    "Check out all the previous product containers, material, labels are removed from the manufacturing area.",
    "Gowning procedure is followed.",
    "Ensure that status board is displayed with mentioning Product Name, Batch No, B. Size, Mfg. Date, Exp.Date & Status with sign & date.",
    "Ensure the absence of batch documents, labels, materials or remnants of previous product or batch on each critical part.",
    "Are the following parts of the tube filling machine cleaned: Hopper, side guards, turret, Tube holders, Cassette etc.",
    "Check and ensure that Balance Calibration & Verification records are updated.",
    "Ensure Environmental conditions are met as per SOP.\nTemperature NMT 28 °C __________\nRelative Humidity (55 ± 10%) __________",
]

TUBE_FILLING_LC_ENDING = [
    "All material from current product have been removed.",
    "All facilities have been cleaned and labeled.",
    "The area has been cleaned and labeled.",
    "All paperwork for the current batch has been completed.",
    "Reconciliation of current batch has been done.",
    "Machine(s) has been checked for cleanliness.",
]

TUBE_FILLING_LC_SPECIAL_FIELDS = {
    'has_environmental': True,
    'environmental_item_index': 8,
}


# ============================================================
# FILM COATING LINE CLEARANCE
# ============================================================
# Coating LC items come from the Product model JSON fields:
#   coating_clearance_start_items  (beginning)
#   coating_clearance_end_items    (ending)
# We define empty defaults here; the template reads from the Product model.
COATING_LC_BEGINNING = []
COATING_LC_ENDING = []
COATING_LC_SPECIAL_FIELDS = {
    'has_environmental': False,
    'uses_product_items': True,  # Items come from Product model, not this config
}


# ============================================================
# PHASES WITH NO LINE CLEARANCE
# ============================================================
# The following phases do NOT have line clearance forms:
# - bmr_creation
# - regulatory_approval
# - quality_control / post_compression_qc / post_mixing_qc / post_blending_qc
# - finished_goods_store
# - final_qa
# - raw_material_release


# ============================================================
# MASTER LOOKUP
# ============================================================
LINE_CLEARANCE_CONFIG = {
    'dispensing': {
        'beginning': DISPENSING_LC_BEGINNING,
        'ending': DISPENSING_LC_ENDING,
        'special': DISPENSING_LC_SPECIAL_FIELDS,
        'title': 'DISPENSING',
    },
    'material_dispensing': {
        'beginning': DISPENSING_LC_BEGINNING,
        'ending': DISPENSING_LC_ENDING,
        'special': DISPENSING_LC_SPECIAL_FIELDS,
        'title': 'DISPENSING',
    },
    'granulation': {
        'beginning': GRANULATION_LC_BEGINNING,
        'ending': GRANULATION_LC_ENDING,
        'special': GRANULATION_LC_SPECIAL_FIELDS,
        'title': 'MIXING/GRANULATION',
    },
    'blending': {
        'beginning': BLENDING_LC_BEGINNING,
        'ending': BLENDING_LC_ENDING,
        'special': BLENDING_LC_SPECIAL_FIELDS,
        'title': 'BLENDING/LUBRICATION',
    },
    'compression': {
        'beginning': COMPRESSION_LC_BEGINNING,
        'ending': COMPRESSION_LC_ENDING,
        'special': COMPRESSION_LC_SPECIAL_FIELDS,
        'title': 'TABLET COMPRESSION',
    },
    'sorting': {
        'beginning': SORTING_LC_BEGINNING,
        'ending': SORTING_LC_ENDING,
        'special': SORTING_LC_SPECIAL_FIELDS,
        'title': 'TABLET INSPECTION & SORTING',
    },
    'post_coating_sorting': {
        'beginning': SORTING_LC_BEGINNING,
        'ending': SORTING_LC_ENDING,
        'special': SORTING_LC_SPECIAL_FIELDS,
        'title': 'POST-COATING INSPECTION & SORTING',
    },
    'blister_packing': {
        'beginning': PACKAGING_LC_BEGINNING,
        'ending': PACKAGING_LC_ENDING,
        'special': PACKAGING_LC_SPECIAL_FIELDS,
        'title': 'PACKAGING',
    },
    'bulk_packing': {
        'beginning': PACKAGING_LC_BEGINNING,
        'ending': PACKAGING_LC_ENDING,
        'special': PACKAGING_LC_SPECIAL_FIELDS,
        'title': 'PACKAGING',
    },
    'secondary_packaging': {
        'beginning': SECONDARY_PACKAGING_LC_BEGINNING,
        'ending': SECONDARY_PACKAGING_LC_ENDING,
        'special': SECONDARY_PACKAGING_LC_SPECIAL_FIELDS,
        'title': 'SECONDARY PACKAGING',
    },
    'mixing': {
        'beginning': MIXING_LC_BEGINNING,
        'ending': MIXING_LC_ENDING,
        'special': MIXING_LC_SPECIAL_FIELDS,
        'title': 'MIXING & HOMOGENIZING',
    },
    'tube_filling': {
        'beginning': TUBE_FILLING_LC_BEGINNING,
        'ending': TUBE_FILLING_LC_ENDING,
        'special': TUBE_FILLING_LC_SPECIAL_FIELDS,
        'title': 'TUBE FILLING',
    },
    'coating': {
        'beginning': COATING_LC_BEGINNING,
        'ending': COATING_LC_ENDING,
        'special': COATING_LC_SPECIAL_FIELDS,
        'title': 'FILM COATING',
    },
    'filling': {
        'beginning': CAPSULE_FILLING_LC_BEGINNING,
        'ending': CAPSULE_FILLING_LC_ENDING,
        'special': CAPSULE_FILLING_LC_SPECIAL_FIELDS,
        'title': 'CAPSULE FILLING',
    },
}

# Phases that have NO line clearance
PHASES_WITHOUT_LC = [
    'bmr_creation',
    'regulatory_approval',
    'raw_material_release',
    'quality_control',
    'post_compression_qc',
    'post_mixing_qc',
    'post_blending_qc',
    'final_qa',
    'finished_goods_store',
    'packaging_material_release',
]


def get_lc_items(phase_name):
    """
    Get the line clearance beginning and ending items for a specific phase.
    
    Returns:
        tuple: (beginning_items, ending_items, config) or (None, None, None) if phase has no LC
    """
    config = LINE_CLEARANCE_CONFIG.get(phase_name)
    if config is None:
        return None, None, None
    return config['beginning'], config['ending'], config


def has_line_clearance(phase_name):
    """Check if a phase has line clearance requirements."""
    return phase_name in LINE_CLEARANCE_CONFIG
