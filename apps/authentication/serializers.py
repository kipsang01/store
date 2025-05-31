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
