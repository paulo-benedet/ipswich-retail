from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from .models import Product


class ClearBasketTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('clear@example.com', 'Testing-73!')
        self.client.force_login(self.user)
        self.product = Product.objects.create(sku='IR-002', name='Tote', price='18.00', stock=8)
        self.client.post(reverse('add_to_basket', args=[self.product.pk]), {'quantity': 2})

    def test_confirmation_and_cancel_preserve_contents(self):
        before = dict(self.client.session['basket'])
        response = self.client.get(reverse('clear_basket'))
        self.assertContains(response, 'Clear your basket?')
        self.assertContains(response, 'Cancel')
        self.assertContains(response, '£36.00')
        self.client.get(reverse('basket'))
        self.assertEqual(self.client.session['basket'], before)
        self.client.post(reverse('clear_basket'), {})
        self.assertEqual(self.client.session['basket'], before)
        self.client.get(reverse('clear_basket') + '?confirm=yes')
        self.assertEqual(self.client.session['basket'], before)

    def test_confirm_clears_all_and_resets_products_summary(self):
        other = Product.objects.create(sku='IR-001', name='Mug', price='12.00', stock=12)
        self.client.post(reverse('add_to_basket', args=[other.pk]), {'quantity': 3})
        response = self.client.post(reverse('clear_basket'), {'confirm': 'yes'}, follow=True)
        self.assertContains(response, 'Your basket is empty')
        self.assertContains(response, 'Your basket has been cleared.')
        self.assertNotContains(response, '>Clear basket</a>')
        self.assertEqual(self.client.session['basket'], {})
        summary = self.client.get(reverse('products')).context['basket_summary']
        self.assertEqual(summary, {'count': 0, 'subtotal': Decimal('0.00')})
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)
        self.client.post(reverse('add_to_basket', args=[self.product.pk]), {'quantity': 1})
        self.assertEqual(self.client.get(reverse('basket')).context['basket_summary']['count'], 1)

    def test_clear_is_session_scoped_and_repeatable(self):
        other = Client()
        other.force_login(self.user)
        other.post(reverse('add_to_basket', args=[self.product.pk]), {'quantity': 1})
        for _ in range(2):
            self.client.post(reverse('clear_basket'), {'confirm': 'yes'})
        self.assertEqual(other.session['basket'], {str(self.product.pk): 1})
        self.assertRedirects(self.client.get(reverse('clear_basket')), reverse('basket'))

    def test_authentication_and_csrf_required(self):
        anonymous = Client()
        self.assertEqual(anonymous.post(reverse('clear_basket'), {'confirm': 'yes'}).status_code, 302)
        secure = Client(enforce_csrf_checks=True)
        secure.force_login(self.user)
        self.assertEqual(secure.post(reverse('clear_basket'), {'confirm': 'yes'}).status_code, 403)
        self.assertEqual(self.client.session['basket'], {str(self.product.pk): 2})
