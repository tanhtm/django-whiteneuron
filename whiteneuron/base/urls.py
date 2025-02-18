from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, re_path
from django.views.static import serve

from .sites import base_admin_site
from .views import HomeView

urlpatterns = []
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
        path("__reload__/", include("django_browser_reload.urls")),
    ]
    
urlpatterns += [
    path("", HomeView.as_view(), name="home"),
    path("i18n/", include("django.conf.urls.i18n")),
]
