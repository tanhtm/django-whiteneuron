from django.urls import path

from . import api

app_name = "notifications"

urlpatterns = [
    path("", api.notification_list, name="list"),
    path("unread-count/", api.unread_count, name="unread_count"),
    path("read-all/", api.mark_all_read, name="read_all"),
    path("<int:pk>/", api.notification_detail, name="detail"),
    path("<int:pk>/read/", api.mark_read, name="read"),
    path("<int:pk>/unread/", api.mark_unread, name="unread"),
]
