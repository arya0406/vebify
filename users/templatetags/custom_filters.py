from django import template

register = template.Library()

@register.filter
def default_if_none(value, default):
    """Returns the default value if the value is None."""
    if value is None:
        return default
    return value

@register.filter
def divide(value, arg):
    """Divides the value by the argument."""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def modulo(value, arg):
    """Returns the remainder of value divided by arg."""
    try:
        return int(value) % int(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0