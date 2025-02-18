from modeltranslation.admin import TabbedTranslationAdmin as DefaultTabbedTranslationAdmin

from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from .utils import gpt_translate_vi

def _gpt_translate_vi_action(admin_obj, request, queryset):
    # print("GPT Translate to Vietnamese")
    # print("Params:")
    # print("self:", admin_obj)
    # print("request:", request)
    # print("queryset:", queryset)

    success = []
    failed = []
    model = admin_obj.model
    message = set()
    for obj in queryset:
        result = gpt_translate_vi(request, obj)
        if result["success"]:
            for key, value in result["result"].items():
                if key.endswith("_vi"):
                    setattr(obj, key, value)
            obj.save()
            success.append(str(obj.__str__()))
        else:
            # messages.error(request, result["message"])
            failed.append(str(obj.__str__()))
            message.add(result["message"])
            pass
    if success:
        messages.success(request, f"Translated successfully: {', '.join(success)}")
    if failed:
        messages.error(request, f"Translated failed: {', '.join(failed)} ({', '.join(message)})")

class TabbedTranslationAdmin(DefaultTabbedTranslationAdmin):
    def get_actions(self, request):
        actions = super().get_actions(request)
        if not "gpt_translate_vi_action" in actions:
            actions["gpt_translate_vi_action"] = (
                _gpt_translate_vi_action,
                "gpt_translate_vi_action",
                _("Translate to Vietnamese"),
            )
        return actions

    