from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import include, path, reverse
from django.utils import timezone

from .models import ReleaseNote, ReleaseNoteView

urlpatterns = [
    path("api/release-notes/", include("whiteneuron.notification.release_urls")),
]


@override_settings(ROOT_URLCONF=__name__, SECURE_SSL_REDIRECT=False)
class ReleaseNoteApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.alice = User.objects.create_user(username="alice", password="x")
        cls.bob = User.objects.create_user(username="bob", password="x")
        now = timezone.now()
        cls.v1 = ReleaseNote.objects.create(version="1.0", title="First", content="**bold**",
                                            is_published=True, published_at=now - timedelta(days=2))
        cls.v2 = ReleaseNote.objects.create(version="1.1", title="Second", content="- a\n- b",
                                            is_published=True, published_at=now - timedelta(days=1))
        cls.draft = ReleaseNote.objects.create(version="2.0", title="Draft", is_published=False)
        cls.future = ReleaseNote.objects.create(version="1.2", title="Scheduled", is_published=True,
                                                published_at=now + timedelta(days=1))

    def setUp(self):
        self.client.force_login(self.alice)

    def test_requires_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("release_notes:list")).status_code, 401)

    def test_list_only_visible(self):
        data = self.client.get(reverse("release_notes:list")).json()
        self.assertEqual([i["version"] for i in data["results"]], ["1.1", "1.0"])
        self.assertEqual(data["unseen_count"], 2)
        self.assertIn("<strong>bold</strong>", data["results"][1]["content_html"])

    def test_latest(self):
        data = self.client.get(reverse("release_notes:latest")).json()
        self.assertEqual(data["result"]["version"], "1.1")
        self.assertFalse(data["result"]["is_seen"])

    def test_latest_empty(self):
        ReleaseNote.objects.all().delete()
        self.assertIsNone(self.client.get(reverse("release_notes:latest")).json()["result"])

    def test_draft_and_scheduled_not_accessible(self):
        for note in (self.draft, self.future):
            self.assertEqual(self.client.get(reverse("release_notes:detail", args=[note.pk])).status_code, 404)
            self.assertEqual(self.client.post(reverse("release_notes:seen", args=[note.pk])).status_code, 404)

    def test_mark_seen_is_per_user_and_idempotent(self):
        url = reverse("release_notes:seen", args=[self.v2.pk])
        self.assertEqual(self.client.post(url).json()["unseen_count"], 1)
        self.assertEqual(self.client.post(url).json()["unseen_count"], 1)
        self.assertEqual(ReleaseNoteView.objects.filter(user=self.alice).count(), 1)

        unseen = self.client.get(reverse("release_notes:unseen")).json()["results"]
        self.assertEqual([i["version"] for i in unseen], ["1.0"])
        self.assertTrue(self.client.get(reverse("release_notes:detail", args=[self.v2.pk])).json()["is_seen"])

        self.client.force_login(self.bob)
        self.assertEqual(len(self.client.get(reverse("release_notes:unseen")).json()["results"]), 2)

    def test_seen_all(self):
        self.client.post(reverse("release_notes:seen", args=[self.v1.pk]))
        r = self.client.post(reverse("release_notes:seen_all"))
        self.assertEqual(r.json(), {"updated": 1, "unseen_count": 0})
        self.assertEqual(self.client.get(reverse("release_notes:unseen")).json()["results"], [])

    def test_seen_requires_post(self):
        self.assertEqual(self.client.get(reverse("release_notes:seen_all")).status_code, 405)
