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


@register.filter
def drum_rows(data):
    """Return list of 10 drum dicts from a flat capsule filling dy dict.
    Usage: {% for drum in dy|drum_rows %}{{ drum.date }}{% endfor %}
    """
    if not isinstance(data, dict):
        return [{}] * 10
    rows = []
    for i in range(1, 11):
        rows.append({
            'no':       str(i),
            'date':     data.get(f'drum_{i}_date', ''),
            'shift':    data.get(f'drum_{i}_shift', ''),
            'operator': data.get(f'drum_{i}_operator', ''),
            'gross':    data.get(f'drum_{i}_gross', ''),
            'tare':     data.get(f'drum_{i}_tare', ''),
            'net':      data.get(f'drum_{i}_net', ''),
        })
    return rows


@register.filter
def ipqc_rows(data):
    """Return list of 20 dicts with t1 and t2 weight data from an ipqc data dict.
    Usage: {% for row in ipqc|ipqc_rows %}{{ row.no }} {{ row.t1_w }} {{ row.t2_w }}{% endfor %}
    """
    if not isinstance(data, dict):
        return [{'no': str(i), 't1_w': '', 't1_e': '', 't1_net': '', 't2_w': '', 't2_e': '', 't2_net': ''} for i in range(1, 21)]
    return [
        {
            'no': str(i),
            't1_w':   data.get(f't1_w{i}', ''),
            't1_e':   data.get(f't1_e{i}', ''),
            't1_net': data.get(f't1_net{i}', ''),
            't2_w':   data.get(f't2_w{i}', ''),
            't2_e':   data.get(f't2_e{i}', ''),
            't2_net': data.get(f't2_net{i}', ''),
        }
        for i in range(1, 21)
    ]
