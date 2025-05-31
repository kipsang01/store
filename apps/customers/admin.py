from django.contrib import admin

from apps.customers.models import Customer

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'phone', 'address', 'city', 'state', 'zip_code', 'is_verified')
