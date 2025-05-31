from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import GoogleOIDCService
from .serializers import GoogleTokenSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def google_auth(request):
    """
    Authenticate user with Google ID token (OIDC)
    Expected payload: {"id_token": "google_id_token"}
    """
    serializer = GoogleTokenSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'error': 'Invalid data', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    id_token = serializer.validated_data['id_token']
    google_user_data = GoogleOIDCService.verify_google_token(id_token)
    if not google_user_data:
        return Response(
            {'error': 'Invalid Google token'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    try:
        user, created = GoogleOIDCService.get_or_create_user(google_user_data)
        tokens = GoogleOIDCService.generate_tokens_for_user(user)

        return Response({
            'tokens': tokens,
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_new_user': created
            },
            'customer': user.customer.to_dict()
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': 'Authentication failed', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def me(request):
    """
    Get current user info (requires authentication)
    """
    user = request.user
    return Response({
        'user': {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        },
        'customer': user.customer.to_dict()
    })


@api_view(['POST'])
def logout(request):
    """
    Blacklist the user's refresh token
    """
    try:
        refresh_token = request.data['refresh']
        token = RefreshToken(refresh_token)
        token.blacklist()
    except Exception as e:
        return Response({'message': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)