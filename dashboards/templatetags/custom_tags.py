from django import template
import re
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='format_phase_name')
def format_phase_name(value):
    """
    Convert snake_case phase name to Title Case with spaces
    Example: finished_goods_store -> Finished Goods Store
    """
    if not value:
        return ""
    # Replace underscores with spaces
    value = value.replace("_", " ")
    # Return title-cased result
    return value.title()

@register.filter(name='make_range')
def make_range(value):
    """
    Returns a range object for iteration.
    Usage: {% for i in 5|make_range %}
    Returns: 1, 2, 3, 4, 5
    """
    try:
        return range(1, int(value) + 1)
    except (ValueError, TypeError):
        return []

@register.filter
def percentage_add(value, percentage):
    """
    Adds a percentage to the value.
    Usage: {{ 100|percentage_add:10 }} -> 110.0
    """
    try:
        val = float(value)
        pct = float(percentage)
        res = val * (1 + pct / 100)
        return f"{res:.1f}"
    except (ValueError, TypeError):
        return ""

@register.filter
def percentage_sub(value, percentage):
    """
    Subtracts a percentage from the value.
    Usage: {{ 100|percentage_sub:10 }} -> 90.0
    """
    try:
        val = float(value)
        pct = float(percentage)
        res = val * (1 - pct / 100)
        return f"{res:.1f}"
    except (ValueError, TypeError):
        return ""


@register.filter
def dict_key(d, key):
    """
    Look up a dynamic key in a dictionary.
    Usage: {{ lc_data|dict_key:"granulation_beginning_item1_operator" }}
    """
    if isinstance(d, dict):
        return d.get(key, '')
    return ''


@register.filter
def intadd(value, arg):
    """Add an integer to a value. Usage: {{ forloop.counter|intadd:20 }}"""
    try:
        return int(value) + int(arg)
    except (ValueError, TypeError):
        return value


@register.filter
def split(value, arg):
    """Split a string by a separator. Usage: {{ "a,b,c"|split:"," }}"""
    if value is None:
        return []
    return str(value).split(str(arg))


@register.filter
def counter_to_alpha(value):
    """Convert 1-based integer to lowercase letter: 1→a, 2→b, etc."""
    try:
        return chr(96 + int(value))
    except (ValueError, TypeError):
        return ''


@register.filter
def get_item(dictionary, key):
    """Access a dict value by variable key. Usage: {{ mydict|get_item:key }}"""
    if not isinstance(dictionary, dict):
        return ''
    return dictionary.get(str(key), '')


@register.simple_tag
def blending_sift_value(blending_data, row, field):
    """
    Look up a blending sift saved value by row number and field.
    Usage: {% blending_sift_value blending_data forloop.counter 'operator' %}
    Builds key: sift_{row}_{field}
    """
    if not isinstance(blending_data, dict):
        return ''
    return blending_data.get(f'sift_{row}_{field}', '')


@register.simple_tag
def blending_equip_mark(blending_data, row_num):
    """Return the saved equipment mark for a given row. Key: equip_{row}_mark"""
    if not isinstance(blending_data, dict):
        return ''
    return blending_data.get(f'equip_{row_num}_mark', '')


@register.simple_tag
def lc_value(lc_data, phase, section, item_num, field):
    """
    Look up a line clearance saved value by building a dynamic key.
    Usage: {% lc_value lc_data 'granulation' 'beginning' forloop.counter 'operator' %}
    Builds key: {phase}_{section}_item{num}_{field}
    """
    if not isinstance(lc_data, dict):
        return ''
    key = f"{phase}_{section}_item{item_num}_{field}"
    value = lc_data.get(key, '')
    if not value:
        # Fallback for non-numeric keys like 'prev' that don't use 'item' prefix
        key2 = f"{phase}_{section}_{item_num}_{field}"
        value = lc_data.get(key2, '')
    return value


@register.simple_tag
def get_phase_lc_items(phase_name, section='beginning'):
    """
    Get LC checklist items for a specific phase from LINE_CLEARANCE_CONFIG.
    Works in both edit mode and view/print mode.
    Usage: {% get_phase_lc_items 'granulation' 'beginning' as items %}
    """
    from workflow.line_clearance_items import get_lc_items
    begin_items, end_items, config = get_lc_items(phase_name)
    if section == 'beginning':
        return begin_items or []
    return end_items or []


@register.filter
def concat(value, arg):
    """Concatenate two values as strings. Usage: {{ "beg_op_"|concat:forloop.counter }}"""
    return str(value) + str(arg)


@register.simple_tag
def get_sec_field(sec_data, field_key, fallback=''):
    """
    Safely get a field value from a section data dict.
    Usage: {% get_sec_field sec_data "beg_op_1" as val %}
    """
    if isinstance(sec_data, dict):
        return sec_data.get(str(field_key), fallback)
    return fallback


@register.filter
def bold_alpha_lines(value):
    """Render multiline text with a./b./c. list lines in bold.

    Useful for procedure blocks where ingredient lines must stand out in print.
    """
    if value is None:
        return ''

    text = str(value)
    lines = text.splitlines()
    rendered = []

    for raw in lines:
        line = raw.strip()
        if not line:
            rendered.append('')
            continue

        if re.match(r'^[a-zA-Z]\.', line):
            rendered.append(f'<strong>{escape(line)}</strong>')
        else:
            rendered.append(escape(line))

    return mark_safe('<br>'.join(rendered))
