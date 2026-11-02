from django.contrib.auth import get_user_model
from django.test import TestCase
from .models import Product


class ProductSearchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user('search@example.com', 'Search-only-73!')
        Product.objects.create(sku='S1', name='Stoneware mug', category='Kitchen', description='A warm start', price='12.00', stock=12)
        Product.objects.create(sku='S2', name='Cotton tote bag', category='Accessories', description='Stoneware is not its name', price='18.00', stock=8)
        Product.objects.create(sku='S3', name='Woven throw', category='Living', price='36.00', stock=0)

    def setUp(self):
        self.client.force_login(self.user)

    def test_partial_case_insensitive_name_search(self):
        for query in ['mug', 'STONE', '  StOnE  ', 'Stoneware mug']:
            with self.subTest(query=query):
                response = self.client.get('/products/', {'q': query})
                self.assertEqual(list(response.context['products'].values_list('sku', flat=True)), ['S1'])
                self.assertContains(response, '1 product')
                self.assertEqual(response.context['query'], query.strip())

    def test_empty_query_restores_catalogue(self):
        for params in [{}, {'q': ''}, {'q': '   '}]:
            self.assertEqual(len(self.client.get('/products/', params).context['products']), 3)

    def test_no_match_has_clear_message(self):
        response = self.client.get('/products/', {'q': 'unknown'})
        self.assertContains(response, 'No products match')
        self.assertContains(response, 'Clear search')
        self.assertEqual(len(response.context['products']), 0)

    def test_unavailable_products_still_searchable(self):
        response = self.client.get('/products/', {'q': 'woven'})
        self.assertContains(response, 'Currently unavailable')
        self.assertContains(response, 'Sold out')

    def test_search_is_literal_and_escaped(self):
        for query in ['%', '_', '<script>alert(1)</script>', "' OR 1=1 --"]:
            with self.subTest(query=query):
                response = self.client.get('/products/', {'q': query})
                self.assertEqual(len(response.context['products']), 0)
                self.assertNotContains(response, '<script>alert(1)</script>')

    def test_anonymous_search_requires_login(self):
        self.client.logout()
        self.assertEqual(self.client.get('/products/', {'q': 'mug'}).status_code, 302)
