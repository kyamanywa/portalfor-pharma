"""
Custom template filters for dashboard templates
"""
from django import template
from django.utils import timezone
from datetime import timedelta

register = template.Library()

@register.filter
def nice_phase_name(value):
    """Convert phase_name with underscores to readable format"""
    if value:
        # Replace underscores with spaces
        value = value.replace("_", " ")
        # Capitalize each word
        return value.title()
    return value

@register.filter
def duration(start_date, end_date):
    """Calculate duration between two dates"""
    if start_date and end_date:
        duration = end_date - start_date
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    return "N/A"

@register.filter
def duration_from_now(start_date):
    """Calculate duration from start_date to now"""
    if start_date:
        now = timezone.now()
        duration = now - start_date
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    return "N/A"

@register.filter
def duration_from_now_hours(start_date):
    """Calculate duration from start_date to now in hours (for priority calculation)"""
    if start_date:
        now = timezone.now()
        duration = now - start_date
        return duration.total_seconds() / 3600
    return 0

@register.filter
def mul(value, arg):
    """Multiplies the value by the argument."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter  
def sub(value, arg):
    """Subtracts the argument from the value."""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def dict_get(d, key):
    """Safe dictionary lookup with a variable key. Usage: {{ mydict|dict_get:varname }}"""
    if isinstance(d, dict):
        return d.get(key)
    return None


@register.filter
def concat(value, arg):
    """Concatenate value and arg as strings. Usage: {{ "prefix_"|concat:loop_counter }}"""
    return str(value) + str(arg)


@register.filter
def dk(d, key):
    """Dict-get shorthand that always returns '' (not None) for missing keys.
    Useful in value attributes: value="{{ ipc|dk:built_key }}"
    """
    if isinstance(d, dict):
        return d.get(str(key), '')
    return ''


@register.filter
def filter_pack_type(materials, pack_type):
    """Filter a list/queryset of PackagingMaterial by pack_type field.
    Usage: {{ packaging_materials|filter_pack_type:"blister" }}
    """
    if materials is None:
        return []
    return [m for m in materials if getattr(m, 'pack_type', None) == pack_type]
