from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from .models import Product


class ReviewBasketTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('review@example.com', 'Testing-73!')
        self.client.force_login(self.user)
        self.product = Product.objects.create(sku='IR-002', name='Cotton tote bag', category='Accessories', price='18.25', stock=8)

    def test_login_required(self):
        self.client.logout()
        response = self.client.get('/basket/')
        self.assertRedirects(response, '/?next=/basket/')

    def test_empty_basket_and_navigation(self):
        response = self.client.get('/basket/')
        self.assertContains(response, 'Your basket is empty')
        self.assertContains(response, 'Browse products')
        self.assertContains(response, '0 items in your basket')
        self.assertContains(response, '£0.00')
        self.assertContains(self.client.get('/products/'), 'href="/basket/">View basket')

    def test_product_details_and_totals(self):
        self.client.post(reverse('add_to_basket', args=[self.product.pk]), {'quantity': 3})
        other = Product.objects.create(sku='IR-001', name='Mug', category='Kitchen', price='12.10', stock=12)
        self.client.post(reverse('add_to_basket', args=[other.pk]), {'quantity': 2})
        response = self.client.get('/basket/')
        for text in ['Cotton tote bag', 'products/IR-002.svg', '£18.25 each', 'Quantity: <strong>3</strong>', '£54.75', '£24.20', '£78.95', '5 items in your basket']:
            self.assertContains(response, text)
        self.assertEqual(response.context['basket_summary']['subtotal'], Decimal('78.95'))
        self.assertIn('no-store', response.headers['Cache-Control'])

    def test_navigation_preserves_basket_and_sessions_are_isolated(self):
        self.client.post(reverse('add_to_basket', args=[self.product.pk]), {'quantity': 2})
        before = dict(self.client.session['basket'])
        for url in ['/basket/', '/products/?q=no-match', '/basket/']:
            self.client.get(url)
        self.assertEqual(self.client.session['basket'], before)
        other = Client(); other.force_login(self.user)
        self.assertContains(other.get('/basket/'), 'Your basket is empty')

    def test_deleted_product_and_current_price_consistency(self):
        self.client.post(reverse('add_to_basket', args=[self.product.pk]), {'quantity': 2})
        Product.objects.filter(pk=self.product.pk).update(price='10.10')
        for url in ['/basket/', '/products/']:
            self.assertEqual(self.client.get(url).context['basket_summary']['subtotal'], Decimal('20.20'))
        self.product.delete()
        self.assertContains(self.client.get('/basket/'), 'Your basket is empty')
