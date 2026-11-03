from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from .models import Product


class BasketTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user('basket@example.com', 'Basket-only-73!')
        cls.product = Product.objects.create(sku='TEST', name='Test mug', category='Kitchen', price='12.00', stock=5)
        cls.sold_out = Product.objects.create(sku='EMPTY', name='Empty', category='Living', price='5.00', stock=0)

    def setUp(self):
        self.client.force_login(self.user)
        self.url = reverse('add_to_basket', args=[self.product.pk])

    def test_add_repeat_and_preserve_filters(self):
        response = self.client.post(self.url, {'quantity': 2, 'q': 'mug', 'category': 'Kitchen'}, follow=True)
        self.assertContains(response, 'Added 2 × Test mug')
        self.assertContains(response, 'In your basket: 2')
        self.assertEqual(response.context['query'], 'mug')
        self.assertEqual(response.context['selected_category'], 'Kitchen')
        self.client.post(self.url, {'quantity': 1})
        self.assertEqual(self.client.session['basket'][str(self.product.pk)], 3)

    def test_invalid_quantities_do_not_change_basket(self):
        self.client.post(self.url, {'quantity': 2})
        for quantity in ['0', '-1', '1.5', 'abc', '', '99999999999999999999']:
            with self.subTest(quantity=quantity):
                response = self.client.post(self.url, {'quantity': quantity}, follow=True)
                self.assertContains(response, 'Choose a positive whole-number quantity.')
                self.assertEqual(self.client.session['basket'][str(self.product.pk)], 2)

    def test_stock_limit_is_cumulative_and_checked_on_server(self):
        self.client.post(self.url, {'quantity': 4})
        response = self.client.post(self.url, {'quantity': 2}, follow=True)
        self.assertContains(response, 'Only 5 units')
        self.assertEqual(self.client.session['basket'][str(self.product.pk)], 4)
        self.client.post(self.url, {'quantity': 1})
        self.assertContains(self.client.get('/products/'), 'Stock limit reached')
        self.client.post(self.url, {'quantity': 1})
        self.assertEqual(self.client.session['basket'][str(self.product.pk)], 5)

    def test_sold_out_post_rejected(self):
        response = self.client.post(reverse('add_to_basket', args=[self.sold_out.pk]), {'quantity': 1}, follow=True)
        self.assertContains(response, 'Empty is currently unavailable.')
        self.assertNotIn(str(self.sold_out.pk), self.client.session['basket'])

    def test_uses_current_stock_not_displayed_stock(self):
        self.client.get('/products/')
        Product.objects.filter(pk=self.product.pk).update(stock=1)
        self.client.post(self.url, {'quantity': 2})
        self.assertEqual(self.client.session['basket'], {})

    def test_navigation_retains_basket_and_other_sessions_are_separate(self):
        self.client.post(self.url, {'quantity': 2})
        self.client.get('/')
        self.client.get('/products/?category=Living')
        self.assertContains(self.client.get('/products/'), 'In your basket: 2')
        other = Client()
        other.force_login(self.user)
        other.get('/products/')
        self.assertEqual(other.session['basket'], {})
        self.assertEqual(self.client.session['basket'][str(self.product.pk)], 2)

    def test_account_switch_does_not_share_basket(self):
        self.client.post(self.url, {'quantity': 2})
        other = get_user_model().objects.create_user('other@example.com', 'Other-only-73!')
        self.client.force_login(other)
        self.client.get('/products/')
        self.assertEqual(self.client.session['basket'], {})

    def test_does_not_reserve_stock(self):
        self.client.post(self.url, {'quantity': 2})
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)

    def test_post_only_and_login_required(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)
        self.client.logout()
        self.assertEqual(self.client.post(self.url, {'quantity': 1}).status_code, 302)
        self.assertNotIn('basket', self.client.session)

    def test_csrf_and_missing_product(self):
        secure = Client(enforce_csrf_checks=True)
        secure.force_login(self.user)
        self.assertEqual(secure.post(self.url, {'quantity': 1}).status_code, 403)
        secure.get('/products/')
        token = secure.cookies['csrftoken'].value
        self.assertEqual(secure.post(self.url, {'quantity': 1, 'csrfmiddlewaretoken': token}).status_code, 302)
        self.assertEqual(self.client.post(reverse('add_to_basket', args=[999999]), {'quantity': 1}).status_code, 404)
