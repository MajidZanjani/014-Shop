"""Display integer minor units without floating point arithmetic."""
from django import template
register = template.Library()


@register.filter
def euro_minor(value):
    if type(value) is not int or value < 0: return 'Pending'
    return '€' + format(value // 100, ',') + '.' + format(value % 100, '02d')
