from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

register = template.Library()


def _resolve_from_sequence(value, part):
    try:
        idx = int(part)
    except (ValueError, TypeError):
        return None
    if isinstance(value, (list, tuple)) and 0 <= idx < len(value):
        return value[idx]
    return None


def _resolve_next(value, part):
    if isinstance(value, dict):
        return value.get(part)
    attr = getattr(value, part, None)
    return attr


@register.simple_tag(takes_context=True)
def resolve_value(context, source_path):
    """Resolve dotted paths or keys from the template context (dicts, objects, lists)."""
    if not source_path:
        return ''
    
    raw_parts = str(source_path).split('.')
    if not raw_parts:
        return ''
    
    if hasattr(context, 'flatten'):
        context_data = context.flatten()
    else:
        context_data = dict(context)

    current = context_data.get(raw_parts[0])
    if current is None:
        return ''

    for part in raw_parts[1:]:
        if current is None:
            return ''
        if isinstance(current, (list, tuple)):
            next_value = _resolve_from_sequence(current, part)
            if next_value is None:
                # Fallback to attribute
                next_value = _resolve_next(current, part)
        else:
            next_value = _resolve_next(current, part)
        current = next_value
        if callable(current):
            try:
                current = current()
            except TypeError:
                break
    return '' if current is None else current


@register.filter
def resolve_template_value(source_path):
    """Simple filter that returns the path - used for backward compatibility"""
    return source_path


@register.filter
def get_item(mapping, key):
    """Safe dict access in templates."""
    if isinstance(mapping, dict):
        return mapping.get(key)
    return None


@register.filter
def resolve_path(value, source_path):
    """Resolve dotted paths from a value (dict/object/list)."""
    if not source_path:
        return ''
    raw_parts = str(source_path).split('.')
    current = value
    for part in raw_parts:
        if current is None:
            return ''
        if isinstance(current, (list, tuple)):
            next_value = _resolve_from_sequence(current, part)
            if next_value is None:
                next_value = _resolve_next(current, part)
        else:
            next_value = _resolve_next(current, part)
        current = next_value
        if callable(current):
            try:
                current = current()
            except TypeError:
                break
    return '' if current is None else current


@register.filter
def pairs(value):
    """
    Split an iterable into 2-item tuples for two-column table layouts.
    Odd-length lists get a trailing (item, None) pair.
    Usage:  {% for left, right in my_list|pairs %}
    """
    lst = list(value) if value else []
    return [(lst[i], lst[i + 1] if i + 1 < len(lst) else None) for i in range(0, len(lst), 2)]


@register.filter
def bmr_value(value):
    """Render saved BMR values with a consistent highlight in view/PDF output."""
    if value is None:
        return ''
    text = str(value)
    if not text.strip() or text.strip() in {'-', '________________'}:
        return text
    return mark_safe(f'<span class="bmr-value-highlight">{conditional_escape(text)}</span>')
