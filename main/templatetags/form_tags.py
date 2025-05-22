from django import template
register = template.Library()

@register.filter(name='getattribute')
def getattribute(value, arg):
    """Gets an attribute of an object dynamically from a string name"""
    if hasattr(value, str(arg)):
        return getattr(value, arg)
    elif hasattr(value, 'get') and value.get(str(arg)):
        return value.get(str(arg))
    elif hasattr(value, 'fields') and arg in value.fields:
         # Attempt to access form field directly if simple getattr fails
         return value[arg] # Use dictionary-like access for forms
    else:
        # Return None or empty string if attribute/field not found
        return None 