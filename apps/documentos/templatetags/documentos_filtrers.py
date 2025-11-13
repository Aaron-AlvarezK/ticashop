from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def filter_by_tipo(documentos, tipo):
    try:
        return documentos.filter(tipo_documento=tipo)
    except Exception:
        return [d for d in documentos if getattr(d, 'tipo_documento', None) == tipo]

@register.filter
def sum_total(documentos):
    total = Decimal('0')
    for d in documentos:
        try:
            total += (d.total or 0)
        except Exception:
            pass
    return total