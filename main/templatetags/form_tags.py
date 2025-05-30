from django import template

register = template.Library()

@register.filter(name='getattribute')
def getattribute(value, arg):
    """Get attribute from form field by name"""
    if hasattr(value, str(arg)):
        return getattr(value, arg)
    elif hasattr(value, 'get') and value.get(str(arg)):
        return value.get(str(arg))
    else:
        return None