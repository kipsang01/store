from django.contrib import admin

from apps.orders.models import Order, OrderItem

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'total_amount')
    search_fields = ('id', 'customer__email')
