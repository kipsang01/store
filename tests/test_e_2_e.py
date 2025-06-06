from django.contrib.auth.models import User
from django.test import TransactionTestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from unittest.mock import patch

from apps.products.models import Category
from apps.products.models import Product
from apps.orders.models import Order
from apps.orders.models import OrderItem
from apps.customers.models import Customer


class CategoryHierarchyIntegrationTest(APITestCase):
    """Test complete category hierarchy workflows"""

    def test_complete_category_hierarchy_workflow(self):
        """Test creating and querying complex category hierarchies"""
        # Create root category
        root_data = {'name': 'All Products'}
        response = self.client.post(reverse('category-list'), root_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        root_id = response.data['id']

        # Create bakery subcategory
        bakery_data = {'name': 'Bakery', 'parent': root_id}
        response = self.client.post(reverse('category-list'), bakery_data)
        bakery_id = response.data['id']

        # Create bread subcategory
        bread_data = {'name': 'Bread', 'parent': bakery_id}
        response = self.client.post(reverse('category-list'), bread_data)
        bread_id = response.data['id']

        # Create produce subcategory
        produce_data = {'name': 'Produce', 'parent': root_id}
        response = self.client.post(reverse('category-list'), produce_data)
        produce_id = response.data['id']

        # Create fruits subcategory
        fruits_data = {'name': 'Fruits', 'parent': produce_id}
        response = self.client.post(reverse('category-list'), fruits_data)
        fruits_id = response.data['id']

        # Test hierarchy display
        response = self.client.get(reverse('category-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should show root categories with nested children
        root_category = next(cat for cat in response.data['results'] if cat['id'] == root_id)
        self.assertEqual(len(root_category['children']), 2)  # Bakery and Produce

        bakery_child = next(child for child in root_category['children'] if child['name'] == 'Bakery')
        self.assertEqual(len(bakery_child['children']), 1)  # Bread

        # Test category paths
        response = self.client.get(reverse('category-all-categories'))
        bread_category = next(cat for cat in response.data if cat['id'] == bread_id)
        self.assertEqual(bread_category['path'], 'All Products > Bakery > Bread')


class ProductCatalogIntegrationTest(APITestCase):
    """Test complete product catalog workflows"""

    def setUp(self):
        self.root = Category.objects.create(name="All Products")
        self.bakery = Category.objects.create(name="Bakery", parent=self.root)
        self.bread = Category.objects.create(name="Bread", parent=self.bakery)
        self.produce = Category.objects.create(name="Produce", parent=self.root)
        self.fruits = Category.objects.create(name="Fruits", parent=self.produce)
#
class OrderWorkflowIntegrationTest(TransactionTestCase):
    """Test complete order workflows with transactions"""

    def setUp(self):
        self.client = APIClient()

        user = User.objects.create_user(
            username="testuser2",
            email="john@example2.com",
            password='testpassword'
        )
        self.client.force_authenticate(user=user)

        Customer.objects.filter(user=user).update(phone='+1234567890')
        self.customer = Customer.objects.get(user=user)

        # Create categories and products
        self.category = Category.objects.create(name="Electronics")
        self.product1 = Product.objects.create(
            name="Laptop", price=Decimal('999.99'),
            category=self.category, sku='ELEC-LAP-001', stock_quantity=10
        )
        self.product2 = Product.objects.create(
            name="Mouse", price=Decimal('29.99'),
            category=self.category, sku='ELEC-MOU-001', stock_quantity=50
        )
        self.product3 = Product.objects.create(
            name="Keyboard", price=Decimal('79.99'),
            category=self.category, sku='ELEC-KEY-001', stock_quantity=25
        )

    @patch('apps.orders.views.send_sms_notification')
    @patch('apps.orders.views.send_admin_email')
    def test_complete_order_workflow_with_notifications(self, mock_email, mock_sms):
        """Test complete order creation workflow with notifications"""
        order_data = {
            'customer': self.customer.id,
            'notes': 'Rush order - needed by Friday',
            'items': [
                {'product': self.product1.id, 'quantity': 1},
                {'product': self.product2.id, 'quantity': 2},
                {'product': self.product3.id, 'quantity': 1}
            ]
        }

        # Create order
        response = self.client.post(reverse('order-list'), order_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        order_id = response.data['id']
        order = Order.objects.get(id=order_id)

        # Verify order details
        expected_total = Decimal('999.99') + (Decimal('29.99') * 2) + Decimal('79.99')  # 1139.96
        self.assertEqual(order.total_amount, expected_total)
        self.assertEqual(order.items.count(), 3)
        self.assertEqual(order.status, 'pending')

        # Verify stock was reduced
        self.product1.refresh_from_db()
        self.product2.refresh_from_db()
        self.product3.refresh_from_db()

        self.assertEqual(self.product1.stock_quantity, 9)  # 10 - 1
        self.assertEqual(self.product2.stock_quantity, 48)  # 50 - 2
        self.assertEqual(self.product3.stock_quantity, 24)  # 25 - 1

        # Verify notifications were called
        mock_sms.assert_called_once()
        mock_email.assert_called_once()

    def test_order_validation_insufficient_stock(self):
        """Test order validation with insufficient stock"""
        order_data = {
            'customer': self.customer.id,
            'items': [
                {'product': self.product1.id, 'quantity': 15}  # Only 10 in stock
            ]
        }

        response = self.client.post(reverse('order-list'), order_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Insufficient stock', str(response.data))

        # Verify no order was created and stock wasn't changed
        self.assertEqual(Order.objects.count(), 0)
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.stock_quantity, 10)

    def test_order_validation_inactive_product(self):
        """Test order validation with inactive product"""
        self.product1.is_active = False
        self.product1.save()

        order_data = {
            'customer': self.customer.id,
            'items': [
                {'product': self.product1.id, 'quantity': 1}
            ]
        }

        response = self.client.post(reverse('order-list'), order_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('not available', str(response.data))

    @patch('apps.orders.views.send_sms_notification')
    def test_order_status_update_workflow(self, mock_sms):
        """Test order status update workflow"""
        order = Order.objects.create(
            customer=self.customer,
            total_amount=Decimal('100.00'),
            status='pending'
        )

        # Update to confirmed
        response = self.client.patch(
            reverse('order-update-status', kwargs={'pk': order.pk}),
            {'status': 'confirmed'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        order.refresh_from_db()
        self.assertEqual(order.status, 'confirmed')

        # Update to shipped (should trigger SMS)
        response = self.client.patch(
            reverse('order-update-status', kwargs={'pk': order.pk}),
            {'status': 'shipped'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        mock_sms.assert_called_once_with(
            self.customer.phone,
            f"Order #{order.id} status updated: Shipped"
        )

        # Test invalid status
        response = self.client.patch(
            reverse('order-update-status', kwargs={'pk': order.pk}),
            {'status': 'invalid_status'}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class EndToEndWorkflowTest(APITestCase):
    """Complete end-to-end workflow tests"""

    def test_complete_ecommerce_workflow(self):
        """Test complete workflow from product creation to order fulfillment"""

        user = User.objects.create_user(
            username='alice',
            email='alice@example.com',
            password='password'
        )
        customer_id = Customer.objects.get(user=user).id

        # 2. Create products with category hierarchy
        products_data = [
            {
                'name': 'MacBook Pro',
                'price': '2499.99',
                'category_path': 'Electronics > Computers > Laptops',
                'sku': 'ELEC-COMP-LAP-001',
                'stock_quantity': 5,
                'description': '16-inch MacBook Pro'
            },
            {
                'name': 'iPhone 15',
                'price': '999.99',
                'category_path': 'Electronics > Mobile > Smartphones',
                'sku': 'ELEC-MOB-PHONE-001',
                'stock_quantity': 20
            },
            {
                'name': 'AirPods Pro',
                'price': '249.99',
                'category_path': 'Electronics > Audio > Headphones',
                'sku': 'ELEC-AUD-HEAD-001',
                'stock_quantity': 15
            }
        ]

        response = self.client.post(reverse('product-bulk-upload'), products_data, format='json')
        self.assertEqual(response.data['total_created'], 3)

        # 3. Verify category hierarchy was created
        electronics = Category.objects.get(name='Electronics')
        self.assertEqual(electronics.get_descendants().__len__(), 8)  # All subcategories

        # 4. Check average prices by category
        laptops_category = Category.objects.get(name='Laptops')
        response = self.client.get(reverse('category-average-price', kwargs={'pk': laptops_category.pk}))
        self.assertEqual(response.data['average_price'], 2499.99)

        smartphones_category = Category.objects.get(name='Smartphones')
        response = self.client.get(reverse('category-average-price', kwargs={'pk': smartphones_category.pk}))
        self.assertEqual(response.data['average_price'], 999.99)

        # 5. Browse products by category
        response = self.client.get(f"{reverse('product-list')}?category={electronics.id}")
        self.assertEqual(len(response.data), 3)  # All electronics products

        # 6. Create order with multiple products
        macbook = Product.objects.get(sku='ELEC-COMP-LAP-001')
        airpods = Product.objects.get(sku='ELEC-AUD-HEAD-001')

        order_data = {
            'customer': customer_id,
            'notes': 'Birthday gift package',
            'items': [
                {'product': macbook.id, 'quantity': 1},
                {'product': airpods.id, 'quantity': 2}
            ]
        }

        with patch('store.utils.send_sms_notification') as mock_sms, \
                patch('store.utils.send_admin_email') as mock_email:

            response = self.client.post(reverse('order-list'), order_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

            order_id = response.data['id']
            expected_total = Decimal('2499.99') + (Decimal('249.99') * 2)  # 2999.97
            self.assertEqual(Decimal(response.data['total_amount']), expected_total)

            # Verify notifications were triggered
            mock_sms.assert_called_once()
            mock_email.assert_called_once()

        # 7. Verify stock was updated
        macbook.refresh_from_db()
        airpods.refresh_from_db()
        self.assertEqual(macbook.stock_quantity, 4)  # 5 - 1
        self.assertEqual(airpods.stock_quantity, 13)  # 15 - 2

        # 8. Update order status through fulfillment
        statuses = ['confirmed', 'shipped', 'delivered']
        for status_val in statuses:
            with patch('store.utils.send_sms_notification') as mock_sms:
                response = self.client.patch(
                    reverse('order-update-status', kwargs={'pk': order_id}),
                    {'status': status_val}
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)

                # SMS should be sent for shipped and delivered
                if status_val in ['shipped', 'delivered']:
                    mock_sms.assert_called_once()

        # 9. Verify final order state
        response = self.client.get(reverse('order-detail', kwargs={'pk': order_id}))
        final_order = response.data
        self.assertEqual(final_order['status'], 'delivered')
        self.assertEqual(len(final_order['items']), 2)
        self.assertEqual(final_order['customer_name'], 'Alice Johnson')

        # 10. Check customer's order history
        response = self.client.get(f"{reverse('order-list')}?customer={customer_id}")
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], order_id)