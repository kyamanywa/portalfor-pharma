from typing import Optional
from .models import ProductTypeConfiguration
from .constants import is_tablet, is_capsule, is_ointment, PRODUCT_TYPES, TABLET_TYPES


def _get_config_by_key(key: str) -> Optional[ProductTypeConfiguration]:
    if not key:
        return None
    try:
        return ProductTypeConfiguration.objects.filter(product_type_key=key).first()
    except Exception:
        return None


def get_product_type_config_for(product) -> Optional[ProductTypeConfiguration]:
    """Return ProductTypeConfiguration for a given Product instance or None."""
    if not product:
        return None
    return _get_config_by_key(getattr(product, 'product_type', None))


def product_has_tag(product, tag: str) -> bool:
    """Return True if the product's configured ProductTypeConfiguration contains the tag.

    Falls back to legacy helpers when no configuration exists.
    """
    if product is None:
        return False

    cfg = get_product_type_config_for(product)
    if cfg and cfg.behavior_tags:
        try:
            return tag in (cfg.behavior_tags or [])
        except Exception:
            # If stored as JSON string fallback
            try:
                import json
                tags = json.loads(cfg.behavior_tags)
                return tag in tags
            except Exception:
                return False

    # Legacy fallbacks for common tags
    key = getattr(product, 'product_type', '')
    if tag == 'tablet-like':
        return is_tablet(key)
    if tag == 'capsule-like':
        return is_capsule(key)
    if tag == 'ointment-like':
        return is_ointment(key)
    if tag == 'requires_coating':
        # Check product attribute first
        if hasattr(product, 'is_coated') and product.is_coated:
            return True
        # No config - assume only tablets may be coated
        return is_tablet(getattr(product, 'product_type', None))

    return False


def product_requires_coating(product) -> bool:
    """Return True if the product should include a coating phase."""
    # Explicit behavior tag wins
    if product_has_tag(product, 'requires_coating'):
        return True
    # Fallback to product attribute
    if hasattr(product, 'is_coated') and product.is_coated:
        return True
    return False


def product_is_tablet_like(product) -> bool:
    return product_has_tag(product, 'tablet-like')


def product_is_capsule_like(product) -> bool:
    return product_has_tag(product, 'capsule-like')


def product_is_ointment_like(product) -> bool:
    return product_has_tag(product, 'ointment-like')


def get_packing_phase_for_product(product) -> Optional[str]:
    """Return the canonical packing phase name for a product.

    Uses ProductTypeConfiguration.default_packing_phase when available, else falls
    back to sensible defaults based on legacy product_type values and tablet_type.
    """
    if product is None:
        return None

    cfg = get_product_type_config_for(product)
    if cfg and cfg.default_packing_phase:
        return cfg.default_packing_phase

    # Legacy fallback logic
    key = getattr(product, 'product_type', '')
    if is_tablet(key):
        tablet_type = getattr(product, 'tablet_type', TABLET_TYPES['NORMAL'])
        if tablet_type and tablet_type == 'tablet_2':
            return 'bulk_packing'
        return 'blister_packing'
    if is_capsule(key):
        return 'blister_packing'
    if is_ointment(key):
        return 'secondary_packaging'

    return None
