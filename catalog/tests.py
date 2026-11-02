from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import TestCase
from .models import Product


class CatalogueTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("buyer@example.com", "test-only-73!")

    def test_requires_login(self):
        self.assertRedirects(self.client.get("/products/"), "/?next=/products/")

    def test_database_products_and_availability(self):
        Product.objects.create(sku="TEST", name="Test mug", category="Home", price=Decimal("8.50"), stock=3)
        Product.objects.create(sku="EMPTY", name="Test pen", category="Stationery", price=Decimal("2.00"), stock=0)
        self.client.force_login(self.user)
        response = self.client.get("/products/")
        for text in ["Test mug", "£8.50", "3 available", "Test pen", "£2.00", "Currently unavailable"]:
            self.assertContains(response, text)
        # Basket controls are deliberately deferred to issue #16.
        self.assertContains(response, "disabled class=\"add")
        self.assertIn("no-store", response.headers["Cache-Control"])

    def test_empty_catalogue(self):
        self.client.force_login(self.user)
        self.assertContains(self.client.get("/products/"), "No products are available")

    def test_seed_is_repeatable_and_preserves_edits(self):
        call_command("seed_products")
        product = Product.objects.get(sku="IR-001")
        product.stock = 1
        product.price = Decimal("9.00")
        product.save()
        call_command("seed_products")
        self.assertEqual(Product.objects.count(), 6)
        product.refresh_from_db()
        self.assertEqual(product.stock, 1)
        self.assertEqual(product.price, Decimal("9.00"))
        self.assertTrue(Product.objects.filter(stock=0).exists())

    def test_negative_stock_and_nonpositive_price_rejected(self):
        for price, stock in [("1.00", -1), ("0.00", 1)]:
            with self.subTest(price=price, stock=stock):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    Product.objects.create(sku="INVALID", name="Invalid", category="Home", price=price, stock=stock)

    def test_legacy_welcome_redirects_to_catalogue(self):
        self.client.force_login(self.user)
        self.assertRedirects(self.client.get("/welcome/"), "/products/")

    def test_correction_migration_preserves_customised_data(self):
        import importlib
        from django.apps import apps
        from django.db import connection
        from types import SimpleNamespace
        Product.objects.create(sku='IR-001', name='Stoneware mug', category='Home', description='A comfortable everyday mug with a glazed finish.', price='8.50', stock=24)
        custom = Product.objects.create(sku='IR-002', name='My custom towels', category='Home', price='15.00', stock=2)
        migration = importlib.import_module('catalog.migrations.0002_align_prototype')
        migration.align_samples(apps, SimpleNamespace(connection=connection))
        product = Product.objects.get(sku='IR-001')
        self.assertEqual(product.price, Decimal('12.00'))
        self.assertEqual(product.stock, 12)
        custom.refresh_from_db()
        self.assertEqual(custom.name, 'My custom towels')
        self.assertEqual(custom.price, Decimal('15.00'))
