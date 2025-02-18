from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.http import HttpResponseRedirect
from django.urls import reverse

from import_export.admin import ImportExportModelAdmin as DefaultImportExportModelAdmin
from unfold.contrib.import_export.forms import ImportForm, ExportForm

from whiteneuron.file_management.models import ExcelFile

from .tasks import export


class ImportExportModelAdmin(DefaultImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = ExportForm

    def has_import_permission(self, request):
        return request.user.is_superuser

    def has_export_permission(self, request):
        return request.user.username != 'guest'

    def export_action(self, request): # Custom export action to export all items with my custom export function
        return self._export_selected_items(request, queryset=None)

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not "export_selected_items" in actions:
            actions["export_selected_items"] = (self.export_action, "export_selected_items", _("Export selected records"))
        return actions

    def _export_selected_items(self, request, queryset=None):
        if queryset is None:
            title = f"Export all {self.model._meta.verbose_name_plural}"
            queryset = self.get_export_queryset(request)
        else:
            title = f"Export selected {self.model._meta.verbose_name_plural}"
        ids = list(queryset.values_list("id", flat=True).all())
        file = ExcelFile(title=title,
                         description=f"""
                            <p> User: {request.user}</p>
                            <p> Exported at: {timezone.now()}</p>
                            <p> Model: {self.model._meta.verbose_name_plural}</p>
                            <p> IDs: {ids[:10]}... (Total: {queryset.count()})</p>
                            """,
                         status='pending',
                         method='auto',
                         created_by=request.user,
                         updated_by=request.user)
        file.save()
        applabel = self.model._meta.app_label
        modelname = self.model._meta.model_name
        # Call export task .delay to run in background
        export.delay(file.id,
                     applabel, modelname, ids,
                     file_name=f"{self.model._meta.verbose_name_plural}.xlsx")

        # Thêm thông báo thành công
        messages.success(request, mark_safe(
            f"Export is in progress. You can download the file when it's ready in <a style='color: red; text-decoration: underline; font-weight: bold;' href='{reverse('admin:file_management_excelfile_change', args=[file.id])}'>here</a>."))

        # Redirect về lại trang admin
        return HttpResponseRedirect(
            reverse(f'admin:{self.model._meta.app_label}_{self.model._meta.model_name}_changelist'))