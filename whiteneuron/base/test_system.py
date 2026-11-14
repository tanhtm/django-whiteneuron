from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import include, path, reverse

urlpatterns = [
    path("api/system/", include("whiteneuron.base.system_urls")),
]


@override_settings(
    ROOT_URLCONF=__name__,
    SECURE_SSL_REDIRECT=False,
    SYSTEM_API_TOKEN="test-token",
    SYSTEM_API_READY_CHECKS=["database", "cache"],
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
)
class SystemApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.admin = User.objects.create_superuser(username="admin", email="a@example.com", password="x")
        cls.user = User.objects.create_user(username="user", password="x")  # is_staff=True by default

    def test_version_is_public(self):
        r = self.client.get(reverse("system:version"))
        self.assertEqual(r.status_code, 200)
        data = r.json()
        for key in ("version", "whiteneuron", "django", "python"):
            self.assertIn(key, data)

    def test_health_is_public(self):
        r = self.client.get(reverse("system:health"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "ok")
        self.assertIn("no-cache", r["Cache-Control"])

    def test_health_rejects_post(self):
        r = self.client.post(reverse("system:health"))
        self.assertEqual(r.status_code, 405)

    def test_ready_ok(self):
        r = self.client.get(reverse("system:ready"))
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(set(data["checks"]), {"database", "cache"})

    def test_ready_failure_returns_503_and_hides_error_from_anonymous(self):
        with mock.patch.dict(
            "whiteneuron.base.system.CHECKS",
            {"cache": mock.Mock(side_effect=RuntimeError("redis down"))},
        ):
            r = self.client.get(reverse("system:ready"))
        self.assertEqual(r.status_code, 503)
        self.assertEqual(r.json()["checks"]["cache"]["status"], "error")
        self.assertNotIn("error", r.json()["checks"]["cache"])

    def test_ready_failure_shows_error_to_superuser(self):
        self.client.force_login(self.admin)
        with mock.patch.dict(
            "whiteneuron.base.system.CHECKS",
            {"cache": mock.Mock(side_effect=RuntimeError("redis down"))},
        ):
            r = self.client.get(reverse("system:ready"))
        self.assertEqual(r.status_code, 503)
        self.assertIn("redis down", r.json()["checks"]["cache"]["error"])

    def test_info_forbidden_for_anonymous_and_staff_user(self):
        self.assertEqual(self.client.get(reverse("system:info")).status_code, 403)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("system:info")).status_code, 403)

    def test_info_wrong_token_forbidden(self):
        r = self.client.get(reverse("system:info"), HTTP_X_SYSTEM_TOKEN="nope")
        self.assertEqual(r.status_code, 403)

    def test_info_for_superuser(self):
        self.client.force_login(self.admin)
        r = self.client.get(reverse("system:info"))
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("uptime_seconds", data["runtime"])
        self.assertEqual(data["database"]["pending_migrations"], 0)
        self.assertEqual(data["checks"]["database"]["status"], "ok")

    def test_info_with_token(self):
        r = self.client.get(reverse("system:info"), HTTP_AUTHORIZATION="Bearer test-token")
        self.assertEqual(r.status_code, 200)
        r = self.client.get(reverse("system:info"), HTTP_X_SYSTEM_TOKEN="test-token")
        self.assertEqual(r.status_code, 200)
