from django.apps import apps
from django.core.exceptions import ImproperlyConfigured

from import_export.resources import modelresource_factory

from apps.base.admin import base_admin_site


def get_resource(app_label: str, model_name: str):
    model = apps.get_model(app_label, model_name)
    admin_instance = base_admin_site._registry.get(model, None)
    if not admin_instance:
        raise ImproperlyConfigured("No admin instance for {}_{}".format(app_label, model_name))
    if not hasattr(admin_instance, 'resource_class') or not admin_instance.resource_class:
        return modelresource_factory(model)
    return admin_instance.resource_class