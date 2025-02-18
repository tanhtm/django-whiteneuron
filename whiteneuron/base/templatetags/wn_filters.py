from unfold.templatetags.unfold_list import register

@register.filter
def get_item(list_obj, index):
    try:
        return list_obj[index]
    except (IndexError, TypeError):
        return None