from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from .models import Product


class CategoryFilterTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user('filter@example.com', 'Filter-only-73!')
        call_command('seed_products')

    def setUp(self):
        self.client.force_login(self.user)

    def test_category_returns_only_matching_products(self):
        for category, count in [('Kitchen', 2), ('Accessories', 1), ('Living', 3)]:
            with self.subTest(category=category):
                response = self.client.get('/products/', {'category': category})
                self.assertEqual(len(response.context['products']), count)
                self.assertTrue(all(p.category == category for p in response.context['products']))
                self.assertContains(response, f'value="{category}" selected')

    def test_all_categories_preserves_search(self):
        response = self.client.get('/products/', {'category': '', 'q': 'mug'})
        self.assertEqual(list(response.context['products'].values_list('name', flat=True)), ['Stoneware mug'])
        self.assertEqual(len(self.client.get('/products/', {'category': ''}).context['products']), 6)

    def test_search_and_filter_intersection_and_no_results(self):
        response = self.client.get('/products/', {'category': 'Kitchen', 'q': 'MUG'})
        self.assertEqual(len(response.context['products']), 1)
        response = self.client.get('/products/', {'category': 'Living', 'q': 'mug'})
        self.assertEqual(len(response.context['products']), 0)
        self.assertContains(response, 'in Living')
        self.assertEqual(response.context['categories'], ['Accessories', 'Kitchen', 'Living'])

    def test_clear_search_preserves_category(self):
        response = self.client.get('/products/', {'category': 'Living', 'q': 'woven'})
        cleared = self.client.get(response.context['clear_search_url'])
        self.assertEqual(cleared.context['selected_category'], 'Living')
        self.assertEqual(len(cleared.context['products']), 3)
        self.assertEqual(cleared.context['query'], '')
        self.assertContains(cleared, 'Currently unavailable')

    def test_dynamic_categories_and_url_encoding(self):
        Product.objects.create(sku='SPECIAL', name='Special', category='Home & garden', price='1.00', stock=1)
        response = self.client.get('/products/', {'category': 'Home & garden', 'q': 'Special'})
        self.assertIn('Home & garden', response.context['categories'])
        self.assertEqual(len(self.client.get(response.context['clear_search_url']).context['products']), 1)

    def test_invalid_category_falls_back_to_all(self):
        response = self.client.get('/products/', {'category': 'Unknown'})
        self.assertEqual(response.context['selected_category'], '')
        self.assertEqual(len(response.context['products']), 6)
