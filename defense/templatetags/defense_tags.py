from django import template
register = template.Library()

@register.filter
def get_score(evaluation, field_name):
    if evaluation is None:
        return 0
    val = getattr(evaluation, field_name, 0)
    return int(val) if val else 0
