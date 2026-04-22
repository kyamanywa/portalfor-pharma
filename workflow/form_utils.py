"""
Utilities for pre-filling BMR forms with product specifications.
"""

from decimal import Decimal


def get_product_specifications_for_form(product):
    """
    Extract all product specifications that can pre-fill BMR forms.
    Returns a dictionary with specification values that forms can use.
    
    Args:
        product: Product model instance
        
    Returns:
        dict: Dictionary of specification values
    """
    if not product:
        return {}
    
    specs = {
        # Label & Product Details
        'label_claim': product.label_claim or '',
        'color_description': product.color_description or '',
        'shelf_life_years': product.shelf_life_years,
        'storage_conditions': product.storage_conditions or '',
        'mfg_license_number': product.mfg_license_number or '',
        'brand_name': product.brand_name or product.product_name,
        'market_type': product.market_type or 'Domestic/Local',
        
        # Tablet/Capsule Physical Specs
        'average_weight_uncoated': product.average_weight_uncoated,
        'weight_tolerance_percentage': product.weight_tolerance_percentage or Decimal('5.0'),
        'hardness_min': product.hardness_min,
        'hardness_max': product.hardness_max,
        'thickness_nominal': product.thickness_nominal,
        'thickness_tolerance': product.thickness_tolerance or Decimal('0.3'),
        'diameter_nominal': product.diameter_nominal,
        'diameter_tolerance': product.diameter_tolerance or Decimal('0.2'),
        'friability_max': product.friability_max or Decimal('1.0'),
        'disintegration_time_max': product.disintegration_time_max,
        
        # Quality Specs
        'dissolution_spec': product.dissolution_spec or '',
        'assay_min_percentage': product.assay_min_percentage or Decimal('95.0'),
        'assay_max_percentage': product.assay_max_percentage or Decimal('105.0'),
        
        # Compression Specs
        'punch_size': product.punch_size,
        'punch_type': product.punch_type or '',
        'upper_punch_description': product.upper_punch_description or '',
        'lower_punch_description': product.lower_punch_description or '',
        'tablet_appearance_trade': product.tablet_appearance_trade or '',
        'tablet_appearance_ug': product.tablet_appearance_ug or '',
        
        # Granulation Parameters
        'lod_min_percentage': product.lod_min_percentage or Decimal('1.60'),
        'lod_max_percentage': product.lod_max_percentage or Decimal('3.60'),
        'drying_temperature': product.drying_temperature,
        'drying_time_minutes': product.drying_time_minutes,
        'dry_mixing_slow_time': product.dry_mixing_slow_time or Decimal('10.0'),
        'dry_mixing_fast_time': product.dry_mixing_fast_time or Decimal('5.0'),
        'wet_mixing_slow_time': product.wet_mixing_slow_time or Decimal('3.0'),
        'wet_mixing_fast_time': product.wet_mixing_fast_time or Decimal('3.0'),
        'milling_sieve_size': product.milling_sieve_size,
        
        # Blending Parameters
        'blending_time_minutes': product.blending_time_minutes or Decimal('20.0'),
        'magnesium_stearate_sieve_mesh': product.magnesium_stearate_sieve_mesh or 40,
        
        # Environmental Specs
        'max_temperature_celsius': product.max_temperature_celsius or Decimal('28.0'),
        'min_humidity_percentage': product.min_humidity_percentage or Decimal('40.0'),
        'max_humidity_percentage': product.max_humidity_percentage or Decimal('65.0'),
        
        # Yield Specs
        'min_yield_percentage': product.min_yield_percentage or Decimal('98.00'),
        'max_yield_percentage': product.max_yield_percentage or Decimal('102.00'),
        
        # Special Instructions
        'special_instructions': product.special_instructions or '',
    }
    
    return specs


def calculate_weight_ranges(product):
    """
    Calculate tablet weight ranges based on product specifications.
    Used for compression form validation.
    
    Args:
        product: Product model instance
        
    Returns:
        dict: Weight range specifications
    """
    if not product or not product.average_weight_uncoated:
        return {}
    
    nominal_weight = product.average_weight_uncoated
    tolerance_pct = product.weight_tolerance_percentage or Decimal('5.0')
    
    # Calculate weight ranges
    weight_plus_5 = nominal_weight * (Decimal('100') + tolerance_pct) / Decimal('100')
    weight_minus_5 = nominal_weight * (Decimal('100') - tolerance_pct) / Decimal('100')
    
    # Alert levels (typical pharmaceutical standards)
    # T1 = ±3%, T2 = ±5%
    weight_plus_3 = nominal_weight * Decimal('1.03')
    weight_minus_3 = nominal_weight * Decimal('0.97')
    
    return {
        'nominal_weight': nominal_weight,
        'tolerance_percentage': tolerance_pct,
        
        # Action levels (±5%)
        'upper_action_limit': weight_plus_5,
        'lower_action_limit': weight_minus_5,
        
        # Good range (±3%)
        'upper_good_limit': weight_plus_3,
        'lower_good_limit': weight_minus_3,
        
        # Range labels for display
        'very_good_range': f"{nominal_weight}mg (Nominal)",
        'good_range': f"{weight_minus_3:.1f}mg to {weight_plus_3:.1f}mg (±3%)",
        'alert_range': f"{weight_minus_5:.1f}mg to {weight_plus_5:.1f}mg (±5%)",
    }


def get_compression_setup_data(product):
    """
    Get compression machine setup data from product specifications.
    
    Args:
        product: Product model instance
        
    Returns:
        dict: Compression setup parameters
    """
    if not product:
        return {}
    
    weight_ranges = calculate_weight_ranges(product)
    
    return {
        'punch_size': product.punch_size,
        'punch_type': product.punch_type or '',
        'upper_punch_description': product.upper_punch_description or '',
        'lower_punch_description': product.lower_punch_description or '',
        'tablet_appearance_trade': product.tablet_appearance_trade or '',
        'tablet_appearance_ug': product.tablet_appearance_ug or '',
        
        # Weight specifications
        'weight_ranges': weight_ranges,
        
        # Physical specifications
        'diameter': {
            'nominal': product.diameter_nominal,
            'tolerance': product.diameter_tolerance or Decimal('0.2'),
            'min': product.diameter_nominal - (product.diameter_tolerance or Decimal('0.2')) if product.diameter_nominal else None,
            'max': product.diameter_nominal + (product.diameter_tolerance or Decimal('0.2')) if product.diameter_nominal else None,
        } if product.diameter_nominal else {},
        
        'thickness': {
            'nominal': product.thickness_nominal,
            'tolerance': product.thickness_tolerance or Decimal('0.3'),
            'min': product.thickness_nominal - (product.thickness_tolerance or Decimal('0.3')) if product.thickness_nominal else None,
            'max': product.thickness_nominal + (product.thickness_tolerance or Decimal('0.3')) if product.thickness_nominal else None,
        } if product.thickness_nominal else {},
        
        'hardness': {
            'min': product.hardness_min,
            'max': product.hardness_max,
            'range': f"{product.hardness_min} - {product.hardness_max} kg/cm²" if product.hardness_min and product.hardness_max else '',
        } if product.hardness_min else {},
        
        'friability_max': product.friability_max or Decimal('1.0'),
        'disintegration_time_max': product.disintegration_time_max,
    }


def get_granulation_setup_data(product):
    """
    Get granulation process setup data from product specifications.
    
    Args:
        product: Product model instance
        
    Returns:
        dict: Granulation setup parameters
    """
    if not product:
        return {}
    
    return {
        # LOD specifications
        'lod_min': product.lod_min_percentage or Decimal('1.60'),
        'lod_max': product.lod_max_percentage or Decimal('3.60'),
        'lod_range': f"{product.lod_min_percentage or Decimal('1.60')}% - {product.lod_max_percentage or Decimal('3.60')}%",
        
        # Drying parameters
        'drying_temp': product.drying_temperature,
        'drying_time': product.drying_time_minutes,
        
        # Mixing times
        'dry_mixing_slow': product.dry_mixing_slow_time or Decimal('10.0'),
        'dry_mixing_fast': product.dry_mixing_fast_time or Decimal('5.0'),
        'wet_mixing_slow': product.wet_mixing_slow_time or Decimal('3.0'),
        'wet_mixing_fast': product.wet_mixing_fast_time or Decimal('3.0'),
        
        # Milling
        'sieve_size': product.milling_sieve_size,
        
        # Environmental
        'max_temp': product.max_temperature_celsius or Decimal('28.0'),
        'min_humidity': product.min_humidity_percentage or Decimal('40.0'),
        'max_humidity': product.max_humidity_percentage or Decimal('65.0'),
    }


def get_blending_setup_data(product):
    """
    Get blending process setup data from product specifications.
    
    Args:
        product: Product model instance
        
    Returns:
        dict: Blending setup parameters
    """
    if not product:
        return {}
    
    return {
        'blending_time': product.blending_time_minutes or Decimal('20.0'),
        'magnesium_stearate_mesh': product.magnesium_stearate_sieve_mesh or 40,
        'lod_min': product.lod_min_percentage or Decimal('1.60'),
        'lod_max': product.lod_max_percentage or Decimal('3.60'),
    }


def get_yield_specifications(product):
    """
    Get yield acceptance criteria from product specifications.
    
    Args:
        product: Product model instance
        
    Returns:
        dict: Yield specifications
    """
    if not product:
        return {
            'min_yield': Decimal('98.00'),
            'max_yield': Decimal('102.00'),
        }
    
    return {
        'min_yield': product.min_yield_percentage or Decimal('98.00'),
        'max_yield': product.max_yield_percentage or Decimal('102.00'),
        'range': f"{product.min_yield_percentage or Decimal('98.00')}% - {product.max_yield_percentage or Decimal('102.00')}%",
    }
