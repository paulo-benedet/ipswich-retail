from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from .models import Product


class CheckoutTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('checkout@example.com', 'Testing-73!')
        self.client.force_login(self.user)
        self.product = Product.objects.create(sku='IR-001', name='Mug', price='12.10', stock=5)
        self.client.post(f'/basket/add/{self.product.pk}/', {'quantity': 2})
        self.data = dict(first_name='Alex', last_name='Taylor', email='alex@example.com', address_line1='12 Example Street', address_line2='', city='Ipswich', postcode='ip11aa')

    def test_summary_and_required_fields(self):
        response = self.client.get('/checkout/')
        self.assertEqual(response.context['basket_summary']['subtotal'], Decimal('24.20'))
        self.assertContains(response, 'Mug')
        self.assertContains(response, 'cash on delivery')
        self.assertNotContains(response, 'Use example delivery details')
        form = response.context['form']
        self.assertFalse(form.fields['address_line2'].required)
        self.assertTrue(all(field.required for name, field in form.fields.items() if name != 'address_line2'))
        self.assertContains(self.client.get('/basket/'), 'href="/checkout/"')

    def test_invalid_details_show_errors_and_preserve_values(self):
        data = dict(self.data, first_name='   ', email='invalid', postcode='123')
        response = self.client.post('/checkout/', data)
        self.assertEqual(set(response.context['form'].errors), {'first_name', 'email', 'postcode'})
        self.assertContains(response, 'Enter your first name.')
        self.assertContains(response, 'value="12 Example Street"')
        self.assertContains(response, 'aria-invalid="true"')
        self.assertFalse(response.context['details_valid'])

    def test_valid_details_do_not_place_order_or_change_basket_stock(self):
        before = dict(self.client.session['basket'])
        response = self.client.post('/checkout/', self.data)
        self.assertTrue(response.context['details_valid'])
        self.assertEqual(response.context['form'].cleaned_data['postcode'], 'IP1 1AA')
        self.assertContains(response, 'No order has been placed.')
        self.assertEqual(self.client.session['basket'], before)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)

    def test_empty_or_deleted_product_basket_cannot_checkout(self):
        self.product.delete()
        for method in [self.client.get, self.client.post]:
            self.assertRedirects(method('/checkout/'), '/basket/')
        session = self.client.session
        session['basket'] = {}
        session.save()
        self.assertRedirects(self.client.get('/checkout/'), '/basket/')

    def test_authentication_csrf_and_methods(self):
        self.assertEqual(Client().get('/checkout/').status_code, 302)
        secure = Client(enforce_csrf_checks=True)
        secure.force_login(self.user)
        self.assertEqual(secure.post('/checkout/', self.data).status_code, 403)
        self.assertEqual(self.client.put('/checkout/').status_code, 405)
        self.assertIn('no-store', self.client.get('/checkout/')['Cache-Control'])
