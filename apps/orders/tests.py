from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.customers.models import Customer
from apps.orders.models import Order, OrderItem
from apps.products.models import Product, Category


class OrderModelTest(TestCase):
    def setUp(self):
        user = User.objects.create_user(
            username="testuser1",
            email="john@example1.com",
            password='testpassword'
        )
        self.customer = Customer.objects.get(
            user=user)
        self.category = Category.objects.create(name="Test Category")
        self.product = Product.objects.create(
            name="Test Product",
            price=Decimal('10.99'),
            category=self.category,
            sku="TEST001",
            stock_quantity=100
        )

    def test_order_creation(self):
        order = Order.objects.create(
            customer=self.customer,
            total_amount=Decimal('21.98')
        )

        order_item = OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=2
        )

        self.assertEqual(order_item.total_price, Decimal('21.98'))
        self.assertEqual(order_item.unit_price, self.product.price)


class OrderAPITest(APITestCase):
    def setUp(self):
        user = User.objects.create_user(
            username="testuser2",
            email="john@example2.com",
            password='testpassword'
        )
        self.customer = Customer.objects.get(
            user=user
        )
        self.category = Category.objects.create(name="Test Category")
        self.product = Product.objects.create(
            name="Test Product",
            price=Decimal('10.99'),
            category=self.category,
            sku="TEST001",
            stock_quantity=100
        )

        self.client.force_authenticate(user=user)


    def test_create_order(self):
        """Test order creation via API"""
        url = reverse('order-list')
        data = {
            'customer': self.customer.pk,
            'notes': 'Test order',
            'items': [
                {
                    'product': self.product.pk,
                    'quantity': 2
                }
            ]
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        order = Order.objects.get(pk=response.data['id'])
        self.assertEqual(order.total_amount, Decimal('21.98'))
        self.assertEqual(order.items.count(), 1)

        # Check stock was reduced
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 98)

    def test_order_insufficient_stock(self):
        """Test order creation with insufficient stock"""
        url = reverse('order-list')
        data = {
            'customer': self.customer.pk,
            'items': [
                {
                    'product': self.product.pk,
                    'quantity': 150
                }
            ]
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_order_status(self):
        """Test order status update"""
        order = Order.objects.create(
            customer=self.customer,
            total_amount=Decimal('10.99')
        )

        url = reverse('order-update-status', kwargs={'pk': order.pk})
        data = {'status': 'shipped'}

        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        order.refresh_from_db()
        self.assertEqual(order.status, 'shipped')