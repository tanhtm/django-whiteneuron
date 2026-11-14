from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import include, path, reverse

from .models import Notification

urlpatterns = [
    path("api/notifications/", include("whiteneuron.notification.urls")),
]


@override_settings(ROOT_URLCONF=__name__, SECURE_SSL_REDIRECT=False)
class NotificationApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.alice = User.objects.create_user(username="alice", password="x")
        cls.bob = User.objects.create_user(username="bob", password="x")
        cls.n1 = Notification.objects.create(user=cls.alice, title="A1", content="c1", flag="info",
                                             changed_data='{"x": 1}', action_by=cls.bob)
        cls.n2 = Notification.objects.create(user=cls.alice, title="A2", content="c2", flag="error")
        cls.n3 = Notification.objects.create(user=cls.alice, title="A3", content="c3", flag="info", is_read=True)
        cls.other = Notification.objects.create(user=cls.bob, title="B1", content="b", flag="info")

    def setUp(self):
        self.client.force_login(self.alice)

    def test_requires_login(self):
        self.client.logout()
        for name in ("notifications:list", "notifications:unread_count"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 401)

    def test_list_only_own_notifications(self):
        r = self.client.get(reverse("notifications:list"))
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["count"], 3)
        self.assertEqual(data["unread_count"], 2)
        self.assertEqual([i["title"] for i in data["results"]], ["A3", "A2", "A1"])
        self.assertNotIn("changed_data", data["results"][0])

    def test_list_filters_and_pagination(self):
        r = self.client.get(reverse("notifications:list"), {"unread": "1"})
        self.assertEqual(r.json()["count"], 2)
        r = self.client.get(reverse("notifications:list"), {"flag": "error"})
        self.assertEqual([i["title"] for i in r.json()["results"]], ["A2"])
        r = self.client.get(reverse("notifications:list"), {"flag": "bogus"})
        self.assertEqual(r.status_code, 400)
        r = self.client.get(reverse("notifications:list"), {"page_size": 2, "page": 2})
        data = r.json()
        self.assertEqual((data["num_pages"], len(data["results"])), (2, 1))
        r = self.client.get(reverse("notifications:list"), {"page": 99})
        self.assertEqual(r.json()["results"], [])

    def test_unread_count(self):
        r = self.client.get(reverse("notifications:unread_count"))
        self.assertEqual(r.json(), {"unread_count": 2})

    def test_detail(self):
        r = self.client.get(reverse("notifications:detail", args=[self.n1.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["changed_data"], '{"x": 1}')
        self.assertEqual(r.json()["action_by"], "bob")

    def test_cannot_access_others_notification(self):
        self.assertEqual(self.client.get(reverse("notifications:detail", args=[self.other.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("notifications:read", args=[self.other.pk])).status_code, 404)
        self.other.refresh_from_db()
        self.assertFalse(self.other.is_read)

    def test_mark_read_and_unread(self):
        r = self.client.post(reverse("notifications:read", args=[self.n1.pk]))
        self.assertEqual(r.json(), {"id": self.n1.pk, "is_read": True, "unread_count": 1})
        r = self.client.post(reverse("notifications:unread", args=[self.n1.pk]))
        self.assertEqual(r.json()["unread_count"], 2)

    def test_read_requires_post(self):
        self.assertEqual(self.client.get(reverse("notifications:read", args=[self.n1.pk])).status_code, 405)

    def test_mark_all_read_only_affects_own(self):
        r = self.client.post(reverse("notifications:read_all"))
        self.assertEqual(r.json(), {"updated": 2, "unread_count": 0})
        self.other.refresh_from_db()
        self.assertFalse(self.other.is_read)

    def test_post_enforces_csrf(self):
        from django.test import Client
        c = Client(enforce_csrf_checks=True)
        c.force_login(self.alice)
        self.assertEqual(c.post(reverse("notifications:read_all")).status_code, 403)
