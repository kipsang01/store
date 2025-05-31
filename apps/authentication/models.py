from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from django.conf import settings
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken

from apps.customers.models import Customer


class GoogleOIDCService:
    """Service to handle Google OIDC authentication"""

    @staticmethod
    def verify_google_token(token):
        """
        Verify Google ID token and return user info
        """
        try:
            idinfo = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                settings.GOOGLE_OAUTH2_CLIENT_ID
            )
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')

            return idinfo

        except ValueError:
            return None

    @staticmethod
    def get_or_create_user(google_user_data):
        """
        Get or create user based on Google user data
        """
        email = google_user_data.get('email')
        if not email:
            raise ValueError('Email not provided by Google')

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email,
                'first_name': google_user_data.get('given_name', ''),
                'last_name': google_user_data.get('family_name', ''),
                'is_active': True,
            }
        )

        if not created:
            user.first_name = google_user_data.get('given_name', user.first_name)
            user.last_name = google_user_data.get('family_name', user.last_name)
            user.save()

        if not hasattr(user, 'customer'):
            Customer.objects.create(user=user)

        return user, created

    @staticmethod
    def generate_tokens_for_user(user):
        """
        Generate JWT tokens for user
        """
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
