"""Display the current explicit EUR fixture; no floating-point rounding."""
from django import template
register=template.Library()


@register.filter
def euro_minor(value):
    if type(value) is not int or value<0:return 'Price to be confirmed'
    whole,fraction=divmod(value,100)
    return f'EUR {whole:,}.{fraction:02d}'
