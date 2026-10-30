"""Display the current explicit EUR fixture; no floating-point rounding."""
from django import template
register=template.Library()


@register.filter
def euro_minor(value):
    if type(value) is not int or value<0:return 'Price to be confirmed'
    whole,fraction=divmod(value,100)
    return f'EUR {whole:,}.{fraction:02d}'


@register.filter
def percentage(value):
    if type(value) is not int or not 0 <= value < 10000: return 'Unavailable'
    whole, fraction = divmod(value, 100)
    return (f'{whole}.{fraction:02d}'.rstrip('0').rstrip('.') if fraction else str(whole)) + '%'
