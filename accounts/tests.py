from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.urls import reverse


class SignInTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.password = 'Test-only-password-73!'
        cls.user = get_user_model().objects.create_user('customer@example.com', cls.password)

    def test_valid_credentials_create_session_and_show_welcome(self):
        response = self.client.post(reverse('login'), {'username': self.user.email, 'password': self.password})
        self.assertRedirects(response, reverse('welcome'))
        self.assertEqual(self.client.session['_auth_user_id'], str(self.user.pk))
        self.assertContains(self.client.get(reverse('welcome')), 'You have signed in successfully')

    def test_invalid_credentials_do_not_authenticate(self):
        for email, password in [('customer@example.com', 'wrong'), ('unknown@example.com', self.password)]:
            with self.subTest(email=email):
                response = self.client.post(reverse('login'), {'username': email, 'password': password})
                self.assertContains(response, 'The email address or password is incorrect.')
                self.assertNotIn('_auth_user_id', self.client.session)
                self.assertNotContains(response, 'value="' + password + '"')

    def test_password_is_hidden(self):
        self.assertContains(self.client.get(reverse('login')), 'type="password"')

    def test_anonymous_welcome_is_protected(self):
        self.assertRedirects(self.client.get(reverse('welcome')), '/?next=/welcome/')

    def test_inactive_account_cannot_sign_in(self):
        self.user.is_active = False
        self.user.save()
        response = self.client.post('/', {'username': self.user.email, 'password': self.password})
        self.assertContains(response, 'The email address or password is incorrect.')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_missing_and_malformed_fields_do_not_authenticate(self):
        for data in [{}, {'username': 'invalid', 'password': self.password}, {'username': self.user.email}]:
            with self.subTest(data=data):
                self.assertEqual(self.client.post('/', data).status_code, 200)
                self.assertNotIn('_auth_user_id', self.client.session)

    def test_email_login_is_case_insensitive(self):
        self.assertRedirects(self.client.post('/', {'username': 'CUSTOMER@EXAMPLE.COM', 'password': self.password}), '/welcome/')

    def test_password_is_hashed(self):
        self.assertNotEqual(self.user.password, self.password)
        self.assertTrue(self.user.check_password(self.password))

    def test_duplicate_email_is_rejected(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            get_user_model().objects.create_user('CUSTOMER@example.com', 'Another-password')

    def test_csrf_is_enforced_and_valid_token_works(self):
        client = Client(enforce_csrf_checks=True)
        credentials = {'username': self.user.email, 'password': self.password}
        self.assertEqual(client.post('/', credentials).status_code, 403)
        client.get('/')
        credentials['csrfmiddlewaretoken'] = client.cookies['csrftoken'].value
        self.assertRedirects(client.post('/', credentials), '/welcome/')

    def test_success_always_uses_temporary_welcome(self):
        self.assertRedirects(self.client.post('/?next=https://example.org', {
            'username': self.user.email, 'password': self.password,
        }), '/welcome/')
    
    def test_controlled_ci_failure(self):
        self.fail("Controlled CI failure")