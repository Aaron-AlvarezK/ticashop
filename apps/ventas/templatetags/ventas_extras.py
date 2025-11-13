from django import template

register = template.Library()

@register.filter
def sum_subtotales(carrito):
    """Suma los subtotales del carrito"""
    try:
        return sum(float(item['subtotal']) for item in carrito)
    except Exception:
        return 0