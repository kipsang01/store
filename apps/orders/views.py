from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.orders.models import Order
from apps.orders.serializers import OrderSerializer, OrderCreateSerializer
from utils.send_email import send_admin_email
from utils.send_sms import send_sms_notification


class OrderViewSet(viewsets.ModelViewSet):

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer

    def get_queryset(self):
        queryset = Order.objects.select_related('customer').prefetch_related('items__product')
        if self.request.user.is_authenticated:
            queryset = queryset.filter(customer__user=self.request.user)
        return queryset

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Create order with notifications"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order = serializer.save()

        for item in order.items.all():
            product = item.product
            product.stock_quantity -= item.quantity
            product.save()

        self.send_notification(order)

        response_serializer = OrderSerializer(order)
        headers = self.get_success_headers(response_serializer.data)

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def send_notification(self, order):
        """Send SMS and email notifications"""
        try:
            order_summary = f"Order #{order.id} confirmed! Total:{order.total_amount}"
            message = (f"Hello {self.request.user.username}, Your Order {order_summary}"
                       f" has been received please be patient while it's being processed")

            if order.customer.phone:
                send_sms_notification(order.customer.phone, message)

            email_body = f"""
                    New Order Placed!

                    Order ID: #{order.id}
                    Customer: {order.customer.user.first_name} {order.customer.user.last_name}
                    Email: {order.customer.user.email}
                    Phone: {order.customer.phone}
                    Total Amount: ${order.total_amount}
                    Order Date: {order.order_date}

                    Items:
                    """

            for item in order.items.all():
                email_body += f"- {item.quantity}x {item.product.name} @ ${item.unit_price} = ${item.total_price}\n"

            if order.notes:
                email_body += f"\nNotes: {order.notes}"
            send_admin_email(f"New Order #{order.id}", email_body)
        except Exception as e:
            print(f"Notification error: {e}")

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update order status"""
        order = self.get_object()
        new_status = request.data.get('status')

        if new_status not in dict(Order.STATUS_CHOICES):
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = new_status
        order.save()

        if new_status in ['shipped', 'delivered']:
            try:
                send_sms_notification(
                    order.customer.phone,
                   f"Order #{order.id} status updated: {new_status.title()}"
                )
            except Exception as e:
                print(f"SMS notification error: {e}")

        serializer = self.get_serializer(order)
        return Response(serializer.data)