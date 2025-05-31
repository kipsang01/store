from rest_framework import serializers

from apps.customers.models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            'id', 'user', 'phone', 'address', 'city',
            'state', 'zip_code',
            'is_verified'
        ]
        read_only_fields = ['id', 'user']
