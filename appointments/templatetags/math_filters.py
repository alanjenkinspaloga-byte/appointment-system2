# ============================================================
# appointments/templatetags/math_filters.py
# Custom template filters for math operations
# ============================================================

from django import template

register = template.Library()


@register.filter
def add(value, arg):
    """Add two numbers."""
    try:
        return float(value) + float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def multiply(value, arg):
    """Multiply two numbers."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter(name='mul')
def mul_filter(value, arg):
    """Multiply two numbers (alias: mul)."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def divide(value, arg):
    """Divide two numbers."""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter(name='divideby')
def divideby_filter(value, arg):
    """Divide two numbers (alias: divideby)."""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter
def subtract(value, arg):
    """Subtract two numbers."""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def percentage(value, total):
    """Calculate percentage of value relative to total."""
    try:
        return (float(value) / float(total)) * 100 if total else 0
    except (ValueError, TypeError, ZeroDivisionError):
        return 0
