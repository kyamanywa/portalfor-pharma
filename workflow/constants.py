"""
Centralized constants for workflow configuration
Extracted from model choices to enable DRY principle and easy maintenance
"""

# ============ PRODUCT TYPES ============
PRODUCT_TYPES = {
    'TABLET': 'tablet',
    'CAPSULE': 'capsule',
    'OINTMENT': 'ointment',
}

PRODUCT_TYPE_CHOICES = [
    (PRODUCT_TYPES['OINTMENT'], 'Ointment'),
    (PRODUCT_TYPES['TABLET'], 'Tablet'),
    (PRODUCT_TYPES['CAPSULE'], 'Capsule'),
]

# ============ TABLET TYPES ============
TABLET_TYPES = {
    'NORMAL': 'normal',
    'TYPE_2': 'tablet_2',
}

TABLET_TYPE_CHOICES = [
    (TABLET_TYPES['NORMAL'], 'Normal Tablet'),
    (TABLET_TYPES['TYPE_2'], 'Tablet Type 2'),
]

# ============ CAPSULE TYPES ============
CAPSULE_TYPES = {
    'NORMAL': 'normal',
    'UG': 'ug',
}

CAPSULE_TYPE_CHOICES = [
    (CAPSULE_TYPES['NORMAL'], 'Normal Capsule (Blister Packing)'),
    (CAPSULE_TYPES['UG'], 'Capsule UG (Bulk Packing)'),
]

# ============ COATING TYPES ============
COATING_TYPES = {
    'COATED': 'coated',
    'UNCOATED': 'uncoated',
}

COATING_TYPE_CHOICES = [
    (COATING_TYPES['UNCOATED'], 'Uncoated'),
    (COATING_TYPES['COATED'], 'Coated'),
]

# ============ PHASE NAMES ============
PHASE_NAMES = {
    # Common phases
    'BMR_CREATION': 'bmr_creation',
    'REGULATORY_APPROVAL': 'regulatory_approval',
    'MATERIAL_DISPENSING': 'material_dispensing',
    'QUALITY_CONTROL': 'quality_control',
    'PACKAGING_MATERIAL_RELEASE': 'packaging_material_release',
    'SECONDARY_PACKAGING': 'secondary_packaging',
    'FINAL_QA': 'final_qa',
    'FINISHED_GOODS_STORE': 'finished_goods_store',
    
    # QC phases
    'POST_COMPRESSION_QC': 'post_compression_qc',
    'POST_MIXING_QC': 'post_mixing_qc',
    'POST_BLENDING_QC': 'post_blending_qc',
    
    # Ointment specific phases
    'MIXING': 'mixing',
    'TUBE_FILLING': 'tube_filling',
    
    # Tablet specific phases
    'GRANULATION': 'granulation',
    'BLENDING': 'blending',
    'COMPRESSION': 'compression',
    'SORTING': 'sorting',
    'COATING': 'coating',
    'POST_COATING_SORTING': 'post_coating_sorting',
    'BLISTER_PACKING': 'blister_packing',
    'BULK_PACKING': 'bulk_packing',
    
    # Capsule specific phases
    'DRYING': 'drying',
    'FILLING': 'filling',
}

PHASE_CHOICES = [
    # Common phases
    (PHASE_NAMES['BMR_CREATION'], 'BMR Creation'),
    (PHASE_NAMES['REGULATORY_APPROVAL'], 'Regulatory Approval'),
    (PHASE_NAMES['MATERIAL_DISPENSING'], 'Material Dispensing'),
    (PHASE_NAMES['QUALITY_CONTROL'], 'Quality Control'),
    (PHASE_NAMES['POST_COMPRESSION_QC'], 'Post-Compression QC'),
    (PHASE_NAMES['POST_MIXING_QC'], 'Post-Mixing QC'),
    (PHASE_NAMES['POST_BLENDING_QC'], 'Post-Blending QC'),
    (PHASE_NAMES['PACKAGING_MATERIAL_RELEASE'], 'Packaging Material Release'),
    (PHASE_NAMES['SECONDARY_PACKAGING'], 'Secondary Packaging'),
    (PHASE_NAMES['FINAL_QA'], 'Final QA'),
    (PHASE_NAMES['FINISHED_GOODS_STORE'], 'Finished Goods Store'),
    
    # Ointment specific phases
    (PHASE_NAMES['MIXING'], 'Mixing'),
    (PHASE_NAMES['TUBE_FILLING'], 'Tube Filling'),
    
    # Tablet specific phases
    (PHASE_NAMES['GRANULATION'], 'Granulation'),
    (PHASE_NAMES['BLENDING'], 'Blending'),
    (PHASE_NAMES['COMPRESSION'], 'Compression'),
    (PHASE_NAMES['SORTING'], 'Sorting'),
    (PHASE_NAMES['COATING'], 'Coating'),
    (PHASE_NAMES['POST_COATING_SORTING'], 'Post-Coating Sorting'),
    (PHASE_NAMES['BLISTER_PACKING'], 'Blister Packing'),
    (PHASE_NAMES['BULK_PACKING'], 'Bulk Packing'),
    
    # Capsule specific phases
    (PHASE_NAMES['DRYING'], 'Drying'),
    (PHASE_NAMES['FILLING'], 'Filling'),
]

# ============ PHASE STATUS ============
PHASE_STATUSES = {
    'PENDING': 'pending',
    'IN_PROGRESS': 'in_progress',
    'COMPLETED': 'completed',
    'FAILED': 'failed',
    'NOT_READY': 'not_ready',
}

PHASE_STATUS_CHOICES = [
    (PHASE_STATUSES['PENDING'], 'Pending'),
    (PHASE_STATUSES['IN_PROGRESS'], 'In Progress'),
    (PHASE_STATUSES['COMPLETED'], 'Completed'),
    (PHASE_STATUSES['FAILED'], 'Failed'),
    (PHASE_STATUSES['NOT_READY'], 'Not Ready'),
]

# ============ BMR STATUS ============
BMR_STATUSES = {
    'DRAFT': 'draft',
    'SUBMITTED': 'submitted',
    'APPROVED': 'approved',
    'REJECTED': 'rejected',
    'IN_PRODUCTION': 'in_production',
    'COMPLETED': 'completed',
    'CANCELLED': 'cancelled',
}

BMR_STATUS_CHOICES = [
    (BMR_STATUSES['DRAFT'], 'Draft'),
    (BMR_STATUSES['SUBMITTED'], 'Submitted'),
    (BMR_STATUSES['APPROVED'], 'Approved'),
    (BMR_STATUSES['REJECTED'], 'Rejected'),
    (BMR_STATUSES['IN_PRODUCTION'], 'In Production'),
    (BMR_STATUSES['COMPLETED'], 'Completed'),
    (BMR_STATUSES['CANCELLED'], 'Cancelled'),
]

# ============ PRODUCT-SPECIFIC PHASE GROUPS ============
# These help identify which phases are specific to which product types

TABLET_PHASES = {
    PHASE_NAMES['GRANULATION'],
    PHASE_NAMES['BLENDING'],
    PHASE_NAMES['COMPRESSION'],
    PHASE_NAMES['SORTING'],
    PHASE_NAMES['COATING'],
    PHASE_NAMES['POST_COATING_SORTING'],
    PHASE_NAMES['POST_COMPRESSION_QC'],
    PHASE_NAMES['BLISTER_PACKING'],
    PHASE_NAMES['BULK_PACKING'],
}

CAPSULE_PHASES = {
    PHASE_NAMES['BLENDING'],
    PHASE_NAMES['POST_BLENDING_QC'],
    PHASE_NAMES['FILLING'],
}

OINTMENT_PHASES = {
    PHASE_NAMES['MIXING'],
    PHASE_NAMES['POST_MIXING_QC'],
    PHASE_NAMES['TUBE_FILLING'],
}

# ============ QC PHASES ============
QC_PHASES = {
    PHASE_NAMES['POST_COMPRESSION_QC'],
    PHASE_NAMES['POST_MIXING_QC'],
    PHASE_NAMES['POST_BLENDING_QC'],
}

# ============ PACKING PHASES ============
PACKING_PHASES = {
    PHASE_NAMES['BLISTER_PACKING'],
    PHASE_NAMES['BULK_PACKING'],
    PHASE_NAMES['TUBE_FILLING'],
}

# ============ HELPER FUNCTIONS ============

def is_tablet(product_type):
    """Check if product type is tablet"""
    return product_type == PRODUCT_TYPES['TABLET']

def is_capsule(product_type):
    """Check if product type is capsule"""
    return product_type == PRODUCT_TYPES['CAPSULE']

def is_ointment(product_type):
    """Check if product type is ointment"""
    return product_type == PRODUCT_TYPES['OINTMENT']

def is_normal_tablet(tablet_type):
    """Check if tablet is normal type"""
    return tablet_type == TABLET_TYPES['NORMAL']

def is_tablet_type_2(tablet_type):
    """Check if tablet is type 2"""
    return tablet_type == TABLET_TYPES['TYPE_2']

def get_packing_phase_for_product(product_type, tablet_type=None):
    """Get the appropriate packing phase for a product"""
    if is_tablet(product_type):
        if tablet_type == TABLET_TYPES['TYPE_2']:
            return PHASE_NAMES['BULK_PACKING']
        else:
            return PHASE_NAMES['BLISTER_PACKING']
    elif is_capsule(product_type):
        return PHASE_NAMES['FILLING']
    elif is_ointment(product_type):
        return PHASE_NAMES['TUBE_FILLING']
    return None

def get_qc_phase_for_product(product_type):
    """Get the QC phase before packing for a product"""
    if is_tablet(product_type):
        return PHASE_NAMES['POST_COMPRESSION_QC']
    elif is_capsule(product_type):
        return PHASE_NAMES['POST_BLENDING_QC']
    elif is_ointment(product_type):
        return PHASE_NAMES['POST_MIXING_QC']
    return None


# ============ DYNAMIC CHOICE FUNCTIONS ============
# These combine hardcoded base choices with database-driven ProductTypeConfiguration

def get_product_type_choices():
    """
    Get all product type choices dynamically from:
    1. Base hardcoded choices (tablet, capsule, ointment)
    2. Custom ProductTypeConfiguration entries from database
    
    Returns list of tuples: [(code, display_name), ...]
    """
    try:
        from workflow.models import ProductTypeConfiguration
        
        # Start with base hardcoded choices
        choices = list(PRODUCT_TYPE_CHOICES)
        
        # Add all active ProductTypeConfiguration entries
        custom_types = ProductTypeConfiguration.objects.filter(is_active=True).values_list(
            'product_type_key', 'product_type_display'
        )
        
        # Add custom types to choices (avoiding duplicates)
        existing_keys = {choice[0] for choice in choices}
        for key, display in custom_types:
            if key not in existing_keys:
                choices.append((key, display))
        
        return choices
    except Exception as e:
        # If database not ready or error, return base choices
        return list(PRODUCT_TYPE_CHOICES)


def get_tablet_type_choices():
    """
    Get tablet type choices.
    Currently returns hardcoded choices (Normal, Type 2)
    Can be extended for custom tablet types if needed.
    """
    return list(TABLET_TYPE_CHOICES)


def get_coating_type_choices():
    """
    Get coating type choices.
    Currently returns hardcoded choices (Coated, Uncoated)
    """
    return list(COATING_TYPE_CHOICES)


def get_phase_choices():
    """
    Get all production phase choices.
    Currently returns hardcoded choices.
    Can be extended for custom phases if needed.
    """
    return list(PHASE_CHOICES)

