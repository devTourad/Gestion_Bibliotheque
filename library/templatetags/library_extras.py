from django import template
from decimal import Decimal

register = template.Library()


@register.filter
def sub(value, arg):
    """Soustrait arg de value"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def multiply(value, arg):
    """Multiplie value par arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def apply_discount(price, discount_percentage):
    """Applique une remise en pourcentage au prix"""
    try:
        price = Decimal(str(price))
        discount = Decimal(str(discount_percentage))
        return price * (1 - discount / 100)
    except (ValueError, TypeError):
        return price


@register.filter
def div(value, arg):
    """Divise value par arg"""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter
def mul(value, arg):
    """Multiplie value par arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.simple_tag
def get_purchase_discount(user_category):
    """Récupère la remise d'achat pour une catégorie d'utilisateur"""
    from library.models import LibraryConfig
    return LibraryConfig.get_purchase_discount(user_category)
