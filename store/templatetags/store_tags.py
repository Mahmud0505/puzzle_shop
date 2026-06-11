from django import template

register = template.Library()

@register.filter
def somoni(value):
    try:
        return '{:,.2f}'.format(float(value)).replace(',', ' ').replace('.', ',') + 'с'
    except (ValueError, TypeError):
        return value
