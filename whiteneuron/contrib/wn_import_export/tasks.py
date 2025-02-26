from django.apps import apps
from django.conf import settings
from django.core.files import File
from django.utils import timezone

import tempfile
from celery import shared_task
from import_export.formats.base_formats import XLSX

from whiteneuron.file_management.models import ExcelFile
from whiteneuron import base

from .utils import get_resource

@shared_task
def export(fileobj_id,
           app_label,
           model_name,
           ids,
           file_name: str):
    # Khởi tạo resource
    fileobj = ExcelFile.objects.get(id=fileobj_id)
    try:
        model = apps.get_model(app_label=app_label, model_name=model_name)
        resource = get_resource(app_label, model_name)()
        # queryset = model.objects.filter(id__in=ids)
        dataset = resource.export(model.objects.all())
        response = XLSX().export_data(dataset)  # byte
        # convert byte to file
        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(response)
            fileobj.file.save(file_name, File(open(tmp.name, 'rb')))
        fileobj.status = 'done'
        fileobj.description += f'<p>Done at: {timezone.now()}</p>'
        fileobj.save()
    except Exception as e:
        fileobj.status = 'error'
        fileobj.title = '[ERROR] ' + fileobj.title
        fileobj.description += f'<p>Error: {str(e)}</p>'
        fileobj.save()
