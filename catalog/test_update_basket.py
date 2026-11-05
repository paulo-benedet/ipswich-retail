from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from .models import Product


class UpdateBasketTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('update@example.com', 'Testing-73!')
        self.client.force_login(self.user)
        self.product = Product.objects.create(sku='IR-001', name='Mug', price='12.10', stock=5)
        self.other = Product.objects.create(sku='IR-002', name='Tote', price='18.25', stock=8)
        for product in [self.product, self.other]:
            self.client.post(reverse('add_to_basket', args=[product.pk]), {'quantity': 2})
        self.update = reverse('update_basket', args=[self.product.pk])
        self.remove = reverse('remove_from_basket', args=[self.product.pk])

    def test_update_replaces_quantity_and_recalculates_totals(self):
        for quantity in [5, 1]:
            response = self.client.post(self.update, {'quantity': quantity}, follow=True)
            self.assertEqual(self.client.session['basket'][str(self.product.pk)], quantity)
            self.assertContains(response, f'£{Decimal("12.10") * quantity:.2f}')
            for url in ['/products/', '/basket/']:
                summary = self.client.get(url).context['basket_summary']
                self.assertEqual(summary['count'], quantity + 2)
                self.assertEqual(summary['subtotal'], Decimal('12.10') * quantity + Decimal('36.50'))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)

    def test_invalid_quantities_preserve_basket(self):
        before = dict(self.client.session['basket'])
        for quantity in ['0', '-1', '1.5', '', 'abc', '6', '999999999999']:
            with self.subTest(quantity=quantity):
                self.client.post(self.update, {'quantity': quantity})
                self.assertEqual(self.client.session['basket'], before)

    def test_stock_is_rechecked_on_submission(self):
        Product.objects.filter(pk=self.product.pk).update(stock=1)
        self.client.post(self.update, {'quantity': 2})
        self.assertEqual(self.client.session['basket'][str(self.product.pk)], 2)
        self.client.post(self.update, {'quantity': 1})
        self.assertEqual(self.client.session['basket'][str(self.product.pk)], 1)
        Product.objects.filter(pk=self.product.pk).update(stock=0)
        response = self.client.post(self.update, {'quantity': 1}, follow=True)
        self.assertContains(response, 'Currently unavailable. Please remove this product.')
        self.assertEqual(self.client.session['basket'][str(self.product.pk)], 1)

    def test_remove_one_then_last_product(self):
        self.client.post(self.remove)
        self.assertEqual(self.client.session['basket'], {str(self.other.pk): 2})
        self.assertEqual(self.client.get('/products/').context['basket_summary']['subtotal'], Decimal('36.50'))
        response = self.client.post(reverse('remove_from_basket', args=[self.other.pk]), follow=True)
        self.assertContains(response, 'Your basket is empty')
        self.assertEqual(self.client.get('/products/').context['basket_summary']['count'], 0)
        self.assertEqual(self.client.post(self.remove).status_code, 302)

    def test_missing_and_deleted_products(self):
        self.client.post(self.remove)
        self.client.post(self.update, {'quantity': 1})
        self.assertNotIn(str(self.product.pk), self.client.session['basket'])
        deleted_id = self.other.pk
        self.other.delete()
        response = self.client.post(reverse('remove_from_basket', args=[deleted_id]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session['basket'], {})

    def test_post_authentication_csrf_and_session_isolation(self):
        before = dict(self.client.session['basket'])
        other = Client(); other.force_login(self.user)
        other.post(self.update, {'quantity': 1}); other.post(self.remove)
        self.assertEqual(self.client.session['basket'], before)
        secure = Client(enforce_csrf_checks=True); secure.force_login(self.user)
        for url in [self.update, self.remove]:
            self.assertEqual(self.client.get(url).status_code, 405)
            self.assertEqual(Client().post(url).status_code, 302)
            self.assertEqual(secure.post(url, {'quantity': 1}).status_code, 403)
        self.assertEqual(self.client.session['basket'], before)
