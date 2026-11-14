from django.urls import path

from . import release_api as api

app_name = "release_notes"

urlpatterns = [
    path("", api.release_note_list, name="list"),
    path("latest/", api.release_note_latest, name="latest"),
    path("unseen/", api.release_note_unseen, name="unseen"),
    path("seen-all/", api.release_note_seen_all, name="seen_all"),
    path("<int:pk>/", api.release_note_detail, name="detail"),
    path("<int:pk>/seen/", api.release_note_seen, name="seen"),
]
