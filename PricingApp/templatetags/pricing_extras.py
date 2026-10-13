"""Filtres de template custom pour Prixio."""
from django import template

register = template.Library()


@register.filter
def first_value(d):
    """Retourne la première valeur d'un dict."""
    if not d or not hasattr(d, "values"):
        return ""
    try:
        return next(iter(d.values()), "")
    except Exception:
        return ""


@register.filter
def get_item(d, key):
    """Retourne d[key] dans un template."""
    if not d or not isinstance(d, dict):
        return ""
    return d.get(key, "")
