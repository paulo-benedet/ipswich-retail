import uuid
from unittest.mock import patch
from django.db import DatabaseError
from django.test import Client, TestCase
from .test_checkout import CheckoutTests
from .models import Order, OrderItem, Product
from .orders import place_order, StockError


class OrderSubmissionTests(TestCase):
    def setUp(self):
        CheckoutTests.setUp(self)
        self.data['submission_token'] = self.client.get('/checkout/').context['submission_token']

    def test_duplicate_submission_and_refresh(self):
        response = self.client.post('/checkout/', self.data)
        target = response['Location']
        self.assertEqual(self.client.post('/checkout/', self.data)['Location'], target)
        self.client.get(target)
        self.client.get(target)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 1)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)
        order = Order.objects.get()
        self.assertEqual(str(order.total), '24.20')
        self.assertEqual(order.payment_method, 'cash_on_delivery')
        Product.objects.filter(pk=self.product.pk).update(price='99.00', name='Changed')
        self.assertEqual(order.items.get().name, 'Mug')
        self.assertEqual(str(order.items.get().unit_price), '12.10')

    def test_stock_failure_rolls_back_every_item(self):
        other = Product.objects.create(sku='IR-002', name='Tote', price='18', stock=2)
        self.client.post(f'/basket/add/{other.pk}/', {'quantity': 2})
        Product.objects.filter(pk=other.pk).update(stock=1)
        before = dict(self.client.session['basket'])
        response = self.client.post('/checkout/', self.data)
        self.assertContains(response, 'Only 1 units of Tote')
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(OrderItem.objects.count(), 0)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)
        self.assertEqual(self.client.session['basket'], before)
        self.assertContains(response, 'value="Alex"')

    def test_database_failure_rolls_back_and_keeps_basket(self):
        with patch('catalog.orders.OrderItem.objects.create', side_effect=DatabaseError('failure')):
            response = self.client.post('/checkout/', self.data)
        self.assertContains(response, 'We could not save your order.')
        self.assertEqual(Order.objects.count(), 0)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)
        self.assertTrue(self.client.session['basket'])

    def test_tampered_token_and_cross_session_confirmation(self):
        response = self.client.post('/checkout/', dict(self.data, submission_token='fake'))
        self.assertContains(response, 'form has expired')
        self.assertFalse(Order.objects.exists())
        response = self.client.post('/checkout/', self.data)
        other = Client(); other.force_login(self.user)
        self.assertRedirects(other.get(response['Location']), '/basket/')
        other.post(f'/basket/add/{self.product.pk}/', {'quantity': 1})
        other.post('/checkout/', self.data)
        self.assertEqual(Order.objects.count(), 1)

    def test_deleted_product_prevents_partial_order(self):
        details = {key: value for key, value in self.data.items() if key != 'submission_token'}
        with self.assertRaises(StockError):
            place_order(self.user, uuid.uuid4(), {str(self.product.pk): 1, '99999': 1}, details)
        self.assertFalse(Order.objects.exists())
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)

    def test_two_orders_cannot_exceed_stock(self):
        details = {key: value for key, value in self.data.items() if key != 'submission_token'}
        place_order(self.user, uuid.uuid4(), {str(self.product.pk): 4}, details)
        with self.assertRaises(StockError):
            place_order(self.user, uuid.uuid4(), {str(self.product.pk): 2}, details)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 1)
        self.assertEqual(Order.objects.count(), 1)
