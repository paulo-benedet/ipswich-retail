from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.management import call_command
from playwright.sync_api import sync_playwright, expect


class CatalogueBrowserTests(StaticLiveServerTestCase):
    def test_login_catalogue_and_mobile_layout(self):
        get_user_model().objects.create_user('browse@example.com', 'Browser-only-73!')
        call_command('seed_products')
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                page = browser.new_page(viewport={'width': 1280, 'height': 900})
                page.goto(self.live_server_url)
                page.get_by_label('Email address').fill('browse@example.com')
                page.get_by_label('Password:', exact=True).fill('Browser-only-73!')
                page.get_by_role('button', name='Sign in', exact=True).click()
                expect(page).to_have_url(self.live_server_url + '/products/')
                expect(page.get_by_role('article')).to_have_count(6)
                expect(page.get_by_role('heading', name='A few good things for your home.')).to_be_visible()
                expect(page.get_by_role('button', name='Sold out', exact=True)).to_be_disabled()
                self.assertTrue(page.locator('.picture img').evaluate_all('(imgs) => imgs.every(img => img.complete && img.naturalWidth > 0)'))
                expect(page.get_by_text('Currently unavailable', exact=True)).to_be_visible()
                expect(page.get_by_text('£12.00', exact=True)).to_be_visible()
                import os
                if os.environ.get('CATALOG_SCREENSHOT_DIR'):
                    page.screenshot(path=os.path.join(os.environ['CATALOG_SCREENSHOT_DIR'], 'catalog-desktop.png'), full_page=True)
                page.set_viewport_size({'width': 390, 'height': 844})
                self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'))
                if os.environ.get('CATALOG_SCREENSHOT_DIR'):
                    page.screenshot(path=os.path.join(os.environ['CATALOG_SCREENSHOT_DIR'], 'catalog-mobile.png'), full_page=True)
            finally:
                browser.close()
