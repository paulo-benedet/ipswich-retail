from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from .models import Product


class BasketSummaryTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('summary@example.com', 'Summary-only-73!')
        self.client.force_login(self.user)
        self.mug = Product.objects.create(sku='MUG', name='Mug', category='Kitchen', price='12.10', stock=12)
        self.bag = Product.objects.create(sku='BAG', name='Bag', category='Accessories', price='18.25', stock=8)

    def add(self, product, quantity):
        return self.client.post(reverse('add_to_basket', args=[product.pk]), {'quantity': quantity}, follow=True)

    def test_empty_and_singular_summary(self):
        response = self.client.get('/products/')
        self.assertContains(response, 'Your basket · 0 items')
        self.assertEqual(response.context['basket_summary']['subtotal'], Decimal('0.00'))
        self.assertContains(self.add(self.mug, 1), 'Your basket · 1 item</span>')

    def test_multiple_products_and_repeated_additions_use_units_and_decimal_prices(self):
        self.add(self.mug, 2)
        self.add(self.mug, 1)
        response = self.add(self.bag, 2)
        self.assertEqual(response.context['basket_summary'], {'count': 5, 'subtotal': Decimal('72.80')})
        self.assertContains(response, 'Your basket · 5 items')
        self.assertContains(response, '£72.80')

    def test_search_category_and_refresh_preserve_whole_basket_summary(self):
        self.add(self.mug, 2)
        self.add(self.bag, 1)
        for url in ['/products/?category=Accessories', '/products/?q=missing', '/products/', '/products/']:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.context['basket_summary'], {'count': 3, 'subtotal': Decimal('42.45')})

    def test_rejected_addition_does_not_inflate_summary(self):
        self.add(self.mug, 2)
        for quantity in [0, -1, '1.5', 11]:
            response = self.add(self.mug, quantity)
            self.assertEqual(response.context['basket_summary'], {'count': 2, 'subtotal': Decimal('24.20')})

    def test_current_prices_and_deleted_products(self):
        self.add(self.mug, 2)
        self.add(self.bag, 1)
        Product.objects.filter(pk=self.mug.pk).update(price='10.50')
        self.bag.delete()
        response = self.client.get('/products/')
        self.assertEqual(response.context['basket_summary'], {'count': 2, 'subtotal': Decimal('21.00')})
