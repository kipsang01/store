from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.orders.models import Order
from apps.orders.serializers import OrderSerializer, OrderCreateSerializer
from utils.send_email import send_admin_email
from utils.send_sms import send_sms_notification


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer

    def get_queryset(self):
        queryset = Order.objects.select_related('customer').prefetch_related('items__product')
        customer_id = self.request.query_params.get('customer', None)

        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)

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
            send_sms_notification(
                phone=order.customer.phone,
                message=f"Order #{order.id} confirmed! Total: ${order.total_amount}"
            )
            send_admin_email(
                subject=f"New Order #{order.id}",
                order=order
            )
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
                    phone=order.customer.phone,
                    message=f"Order #{order.id} status updated: {new_status.title()}"
                )
            except Exception as e:
                print(f"SMS notification error: {e}")

        serializer = self.get_serializer(order)
        return Response(serializer.data)