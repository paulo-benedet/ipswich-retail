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
                page.wait_for_function("() => { const imgs = [...document.querySelectorAll('.picture img')]; return imgs.length === 6 && imgs.every(img => img.complete && img.naturalWidth > 0); }")
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

    def test_search_and_clear_in_browser(self):
        get_user_model().objects.create_user('search@example.com', 'Browser-only-73!')
        call_command('seed_products')
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                page = browser.new_page(viewport={'width': 390, 'height': 844})
                page.goto(self.live_server_url)
                page.get_by_label('Email address').fill('search@example.com')
                page.get_by_label('Password:', exact=True).fill('Browser-only-73!')
                page.get_by_role('button', name='Sign in', exact=True).click()
                search = page.get_by_role('searchbox', name='Search products')
                search.fill('StOnE')
                search.press('Enter')
                expect(page.get_by_role('article')).to_have_count(1)
                expect(page.get_by_role('heading', name='Stoneware mug')).to_be_visible()
                expect(search).to_have_value('StOnE')
                search.fill('no-such-product')
                search.press('Enter')
                expect(page.get_by_role('status')).to_contain_text('No products match')
                page.get_by_role('link', name='Clear search', exact=True).click()
                expect(page.get_by_role('article')).to_have_count(6)
                expect(search).to_have_value('')
                search.fill('mug')
                search.press('Enter')
                search.fill('')
                search.press('Enter')
                expect(page.get_by_role('article')).to_have_count(6)
                self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'))
            finally:
                browser.close()

    def test_category_filter_combines_with_search(self):
        get_user_model().objects.create_user('filter@example.com', 'Browser-only-73!')
        call_command('seed_products')
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                page = browser.new_page(viewport={'width': 390, 'height': 844})
                page.goto(self.live_server_url)
                page.get_by_label('Email address').fill('filter@example.com')
                page.get_by_label('Password:', exact=True).fill('Browser-only-73!')
                page.get_by_role('button', name='Sign in', exact=True).click()
                category = page.get_by_label('Category', exact=True)
                search = page.get_by_role('searchbox', name='Search products')
                category.select_option('Kitchen')
                expect(page.get_by_role('article')).to_have_count(2)
                search.fill('MUG')
                search.press('Enter')
                expect(page.get_by_role('article')).to_have_count(1)
                category.select_option('Living')
                expect(page.get_by_role('status')).to_contain_text('No products match')
                expect(search).to_have_value('MUG')
                page.get_by_role('link', name='Clear search', exact=True).click()
                expect(page.get_by_role('article')).to_have_count(3)
                expect(category).to_have_value('Living')
                expect(search).to_have_value('')
                category.select_option('')
                expect(page.get_by_role('article')).to_have_count(6)
                self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'))
            finally:
                browser.close()

    def test_add_quantity_stock_limit_and_session_persistence(self):
        get_user_model().objects.create_user('basket@example.com', 'Browser-only-73!')
        call_command('seed_products')
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                page = browser.new_page(viewport={'width': 390, 'height': 844})
                page.goto(self.live_server_url)
                page.get_by_label('Email address').fill('basket@example.com')
                page.get_by_label('Password:', exact=True).fill('Browser-only-73!')
                page.get_by_role('button', name='Sign in', exact=True).click()
                card = page.get_by_role('article').filter(has=page.get_by_role('heading', name='Stoneware mug', exact=True))
                quantity = card.get_by_role('spinbutton')
                summary = page.get_by_role('complementary', name='Basket summary')
                expect(summary).to_contain_text('Your basket · 0 items')
                expect(summary).to_contain_text('£0.00')
                expect(quantity).to_have_value('1')
                card.get_by_role('button', name='Increase quantity for Stoneware mug', exact=True).click()
                expect(quantity).to_have_value('2')
                card.get_by_role('button', name='+ Add to basket', exact=True).click()
                expect(page.get_by_role('status')).to_contain_text('Added 2 × Stoneware mug')
                expect(card.get_by_text('In your basket: 2', exact=True)).to_be_visible()
                expect(summary).to_contain_text('Your basket · 2 items')
                expect(summary).to_contain_text('£24.00')
                import os
                if os.environ.get('CATALOG_SCREENSHOT_DIR'):
                    page.screenshot(path=os.path.join(os.environ['CATALOG_SCREENSHOT_DIR'], 'summary-mobile.png'), full_page=True)
                    page.set_viewport_size({'width': 1280, 'height': 900})
                    page.screenshot(path=os.path.join(os.environ['CATALOG_SCREENSHOT_DIR'], 'summary-desktop.png'), full_page=True)
                    page.set_viewport_size({'width': 390, 'height': 844})
                page.get_by_label('Category', exact=True).select_option('Living')
                expect(page.get_by_role('button', name='Sold out', exact=True)).to_be_disabled()
                expect(summary).to_contain_text('£24.00')
                page.get_by_label('Category', exact=True).select_option('Kitchen')
                expect(card.get_by_text('In your basket: 2', exact=True)).to_be_visible()
                expect(summary).to_contain_text('Your basket · 2 items')
                expect(summary).to_contain_text('£24.00')
                quantity.fill('10')
                card.get_by_role('button', name='+ Add to basket', exact=True).click()
                expect(card.get_by_text('In your basket: 12', exact=True)).to_be_visible()
                expect(card.get_by_role('button', name='Stock limit reached')).to_be_disabled()
                page.reload()
                expect(summary).to_contain_text('Your basket · 12 items')
                expect(summary).to_contain_text('£144.00')
                expect(card.get_by_text('In your basket: 12', exact=True)).to_be_visible()
                self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'))
            finally:
                browser.close()
