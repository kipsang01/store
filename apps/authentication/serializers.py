from rest_framework import serializers
from django.contrib.auth.models import User
from apps.customers.models import Customer


class GoogleTokenSerializer(serializers.Serializer):
    """Serializer for Google ID token authentication"""
    id_token = serializers.CharField(required=True, help_text="Google ID token")


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class CustomerSerializer(serializers.ModelSerializer):
    """Serializer for Customer model"""
    user = UserSerializer(read_only=True)

    class Meta:
        model = Customer
        fields = [
            'id', 'user', 'phone', 'address', 'city',
            'state', 'zip_code', 'date_of_birth',
            'is_verified'
        ]
        read_only_fields = ['id', 'user']


class CustomerUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating customer profile"""

    class Meta:
        model = Customer
        fields = ['phone', 'address', 'city', 'state', 'zip_code', 'date_of_birth']