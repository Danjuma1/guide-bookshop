from django import template
from django.contrib.humanize.templatetags.humanize import intcomma

register = template.Library()

@register.filter
def split(value, arg):
    """Split a string by the given delimiter"""
    return value.split(arg)

@register.filter
def in_list(value, csv_string):
    """Return True if value is in a comma-separated list of names."""
    return str(value) in [s.strip() for s in csv_string.split(',')]

@register.filter
def currency(value):
    """Format a number as currency with comma thousands separator, no decimals."""
    try:
        return intcomma(int(round(float(value))))
    except (ValueError, TypeError):
        return value