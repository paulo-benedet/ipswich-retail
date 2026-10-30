from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings


class DemoTests(TestCase):
    def test_provision_is_idempotent_and_unprivileged(self):
        call_command('provision_demo')
        call_command('provision_demo')
        self.assertEqual(get_user_model().objects.count(), 1)
        user = get_user_model().objects.get()
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.check_password(settings.DEMO_PASSWORD))
        self.assertRedirects(self.client.post('/', {'username': settings.DEMO_EMAIL, 'password': settings.DEMO_PASSWORD}), '/welcome/')

    def test_existing_account_cannot_be_overwritten(self):
        user = get_user_model().objects.create_user(settings.DEMO_EMAIL, 'Private-password-73!')
        with self.assertRaises(CommandError):
            call_command('provision_demo')
        user.refresh_from_db()
        self.assertTrue(user.check_password('Private-password-73!'))

    @override_settings(DEMO_ENABLED=False)
    def test_disabled_demo_not_exposed_or_created(self):
        call_command('provision_demo')
        self.assertFalse(get_user_model().objects.exists())
        self.assertNotContains(self.client.get('/'), 'id="use-demo"')
        self.assertNotContains(self.client.get('/'), settings.DEMO_PASSWORD)
