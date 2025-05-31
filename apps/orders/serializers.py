from rest_framework import serializers

from apps.orders.models import Order, OrderItem
from apps.products.models import Product


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'quantity', 'unit_price', 'total_price']
        read_only_fields = ['total_price', 'unit_price']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.__str__', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'customer', 'customer_name', 'status',
            'total_amount', 'order_date', 'notes', 'items'
        ]
        read_only_fields = ['total_amount']


class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, write_only=True)

    class Meta:
        model = Order
        fields = ['customer', 'notes', 'items']

    def create(self, validated_data):
        items_data = validated_data.pop('items')

        total_amount = sum(
            item_data['quantity'] * Product.objects.get(id=item_data['product'].id).price
            for item_data in items_data
        )

        order = Order.objects.create(total_amount=total_amount, **validated_data)

        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)

        return order

    def validate_items(self, items_data):
        if not items_data:
            raise serializers.ValidationError("Order must contain at least one item")

        for item_data in items_data:
            product = item_data['product']
            quantity = item_data['quantity']

            if not product.is_active:
                raise serializers.ValidationError(f"Product {product.name} is not available")

            if product.stock_quantity < quantity:
                raise serializers.ValidationError(
                    f"Insufficient stock for {product.name}. Available: {product.stock_quantity}"
                )

        return items_data