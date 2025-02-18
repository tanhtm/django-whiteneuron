from unfold.templatetags.unfold_list import result_list, register, InclusionAdminNode, Parser, Token

@register.tag(name="result_list_grid")
def result_list_grid_tag(parser: Parser, token: Token) -> InclusionAdminNode:
    return InclusionAdminNode(
        parser,
        token,
        func=result_list,
        template_name="grid_view_results.html",
    )