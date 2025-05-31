from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


from apps.products.models import Category, Product


class CategoryModelTest(TestCase):
    def setUp(self):
        self.root = Category.objects.create(name="All Products")
        self.bakery = Category.objects.create(name="Bakery", parent=self.root)
        self.bread = Category.objects.create(name="Bread", parent=self.bakery)

    def test_category_hierarchy(self):
        self.assertEqual(self.bread.parent, self.bakery)
        self.assertEqual(self.bakery.parent, self.root)
        self.assertIsNone(self.root.parent)

    def test_get_ancestors(self):
        ancestors = list(self.bread.get_ancestors())
        self.assertEqual(len(ancestors), 2)
        self.assertIn(self.root, ancestors)
        self.assertIn(self.bakery, ancestors)

    def test_get_descendants(self):
        descendants = self.root.get_descendants()
        self.assertEqual(len(descendants), 2)
        self.assertIn(self.bakery, descendants)
        self.assertIn(self.bread, descendants)


class ProductModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Test Category")
        self.product = Product.objects.create(
            name="Test Product",
            price=Decimal('10.99'),
            category=self.category,
            sku="TEST001",
            stock_quantity=100
        )

    def test_product_creation(self):
        self.assertEqual(self.product.name, "Test Product")
        self.assertEqual(self.product.price, Decimal('10.99'))
        self.assertEqual(self.product.category, self.category)
        self.assertTrue(self.product.is_active)


class CategoryAPITest(APITestCase):
    def setUp(self):

        user = User.objects.create_user(
            username="testuser",
            email="john@example.com",
            password='testpassword'
        )
        self.client.force_authenticate(user=user)

        self.root = Category.objects.create(name="All Products")
        self.bakery = Category.objects.create(name="Bakery", parent=self.root)
        self.bread = Category.objects.create(name="Bread", parent=self.bakery)

        self.product1 = Product.objects.create(
            name="Sourdough",
            price=Decimal('5.99'),
            category=self.bread,
            sku="BREAD001",
            stock_quantity=50
        )
        self.product2 = Product.objects.create(
            name="Baguette",
            price=Decimal('3.99'),
            category=self.bread,
            sku="BREAD002",
            stock_quantity=30
        )

    def test_category_average_price(self):
        url = reverse('category-average-price', kwargs={'pk': self.bread.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['average_price'],  Decimal('4.99'))  # (5.99 + 3.99) / 2
        self.assertEqual(response.data['product_count'], 2)

    def test_category_hierarchy_average_price(self):
        url = reverse('category-average-price', kwargs={'pk': self.bakery.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['average_price'],  Decimal('4.99'))


class ProductAPITest(APITestCase):
    def setUp(self):
        user = User.objects.create_user(
            username="testuser",
            email="john@example.com",
            password='testpassword'
        )
        self.client.force_authenticate(user=user)
        self.category = Category.objects.create(name="Test Category")

    def test_create_product(self):
        url = reverse('product-list')
        data = {
            'name': 'Test Product',
            'price': '19.99',
            'category': self.category.pk,
            'sku': 'TEST001',
            'stock_quantity': 100
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 1)

    def test_bulk_upload_products(self):
        url = reverse('product-bulk-upload')
        data = [
            {
                'name': 'Product 1',
                'price': '10.99',
                'category': self.category.pk,
                'sku': 'PROD001',
                'stock_quantity': 100
            },
            {
                'name': 'Product 2',
                'price': '15.99',
                'category': self.category.pk,
                'sku': 'PROD002',
                'stock_quantity': 50
            }
        ]

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_created'], 2)
        self.assertEqual(Product.objects.count(), 2)