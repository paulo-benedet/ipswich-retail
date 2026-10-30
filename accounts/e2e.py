from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from playwright.sync_api import sync_playwright, expect


class PasswordToggleBrowserTests(StaticLiveServerTestCase):
    def test_toggle_preserves_password_and_allows_login(self):
        secret = "Browser-test-only-73!"
        get_user_model().objects.create_user("browser@example.com", secret)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            try:
                page = browser.new_page()
                page.goto(self.live_server_url)
                password = page.get_by_label("Password:", exact=True)
                password.fill(secret)
                expect(password).to_have_attribute("type", "password")
                page.get_by_role("button", name="Show password").click()
                expect(password).to_have_attribute("type", "text")
                expect(password).to_have_value(secret)
                expect(page).to_have_url(self.live_server_url + "/")
                # A native button must also work from the keyboard.
                page.get_by_role("button", name="Hide password").press("Enter")
                expect(password).to_have_attribute("type", "password")
                expect(password).to_have_value(secret)
                page.get_by_label("Email address").fill("browser@example.com")
                page.get_by_role("button", name="Sign in", exact=True).click()
                expect(page).to_have_url(self.live_server_url + "/welcome/")
                expect(page.get_by_text("You have signed in successfully", exact=False)).to_be_visible()
            finally:
                browser.close()

    def test_demo_fills_without_signing_in_then_authenticates(self):
        from django.conf import settings
        from django.core.management import call_command
        call_command('provision_demo')
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            try:
                page = browser.new_page()
                page.goto(self.live_server_url)
                page.get_by_role('button', name='Show password').click()
                page.get_by_role('button', name='Use demo details').click()
                expect(page.get_by_label('Email address')).to_have_value(settings.DEMO_EMAIL)
                password = page.get_by_label('Password:', exact=True)
                expect(password).to_have_value(settings.DEMO_PASSWORD)
                expect(password).to_have_attribute('type', 'password')
                expect(page).to_have_url(self.live_server_url + '/')
                # Protected welcome still redirects: filling the form did not log in.
                page.goto(self.live_server_url + '/welcome/')
                expect(page).to_have_url(self.live_server_url + '/?next=/welcome/')
                page.get_by_role('button', name='Use demo details').click()
                page.get_by_role('button', name='Sign in', exact=True).click()
                expect(page).to_have_url(self.live_server_url + '/welcome/')
            finally:
                browser.close()
