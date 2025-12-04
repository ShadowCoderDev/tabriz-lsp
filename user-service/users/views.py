from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from drf_spectacular.utils import extend_schema, OpenApiResponse
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    UserUpdateSerializer
)
from .models import User
from .utils import set_jwt_cookies, delete_jwt_cookies, set_access_token_cookie


class RegisterView(generics.CreateAPIView):
    """View for user registration."""
    
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer

    @extend_schema(
        summary="Register a new user",
        description="Create a new user account with email and password. JWT tokens will be set as HTTP-only cookies.",
        responses={
            201: OpenApiResponse(
                description="User successfully created. Tokens are set as HTTP-only cookies.",
                response=UserProfileSerializer
            ),
            400: OpenApiResponse(description="Validation error")
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        # Return user data only (tokens are in HTTP-only cookies)
        user_data = UserProfileSerializer(user).data
        response = Response({
            'user': user_data,
            'message': 'Registration successful. JWT tokens are set as HTTP-only cookies.'
        }, status=status.HTTP_201_CREATED)
        
        # Set tokens as HTTP-only cookies
        set_jwt_cookies(response, access_token, refresh_token)
        
        return response


@extend_schema(
    summary="User login",
    description="Authenticate user. JWT tokens will be set as HTTP-only cookies.",
    responses={
        200: OpenApiResponse(
            description="Login successful. Tokens are set as HTTP-only cookies.",
            response={
                'type': 'object',
                'properties': {
                    'user': {'type': 'object'},
                    'message': {'type': 'string'}
                }
            }
        ),
        400: OpenApiResponse(description="Invalid credentials")
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """View for user login."""
    serializer = UserLoginSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        # Return user data only (tokens are in HTTP-only cookies)
        user_data = UserProfileSerializer(user).data
        response = Response({
            'user': user_data,
            'message': 'Login successful. JWT tokens are set as HTTP-only cookies.'
        }, status=status.HTTP_200_OK)
        
        # Set tokens as HTTP-only cookies
        set_jwt_cookies(response, access_token, refresh_token)
        
        return response
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """View for retrieving and updating user profile."""
    
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        """Return the current authenticated user."""
        return self.request.user

    def get_serializer_class(self):
        """Return appropriate serializer based on request method."""
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserProfileSerializer

    @extend_schema(
        summary="Get user profile",
        description="Retrieve the authenticated user's profile information",
        responses={
            200: OpenApiResponse(
                description="Profile retrieved successfully",
                response=UserProfileSerializer
            ),
            401: OpenApiResponse(description="Authentication required")
        }
    )
    def get(self, request, *args, **kwargs):
        """Retrieve user profile."""
        serializer = self.get_serializer(self.get_object())
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Update user profile",
        description="Update the authenticated user's profile information",
        responses={
            200: OpenApiResponse(
                description="Profile updated successfully",
                response=UserProfileSerializer
            ),
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Authentication required")
        }
    )
    def put(self, request, *args, **kwargs):
        """Update user profile (full update)."""
        return self.update(request, *args, **kwargs)

    @extend_schema(
        summary="Partial update user profile",
        description="Partially update the authenticated user's profile information",
        responses={
            200: OpenApiResponse(
                description="Profile updated successfully",
                response=UserProfileSerializer
            ),
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Authentication required")
        }
    )
    def patch(self, request, *args, **kwargs):
        """Partially update user profile."""
        return self.partial_update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Handle profile update."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Return updated profile using UserProfileSerializer
        profile_serializer = UserProfileSerializer(instance)
        return Response(profile_serializer.data, status=status.HTTP_200_OK)


class CookieTokenRefreshView(TokenRefreshView):
    """
    Custom token refresh view that reads refresh token from HTTP-only cookie.
    Returns new access token as HTTP-only cookie.
    """
    
    @extend_schema(
        summary="Refresh access token",
        description="Refresh access token using refresh token from HTTP-only cookie. New access token will be set as HTTP-only cookie.",
        responses={
            200: OpenApiResponse(
                description="Token refreshed successfully. New access token is set as HTTP-only cookie.",
                response={
                    'type': 'object',
                    'properties': {
                        'message': {'type': 'string'}
                    }
                }
            ),
            401: OpenApiResponse(description="Invalid or expired refresh token")
        }
    )
    def post(self, request, *args, **kwargs):
        # Get refresh token from cookie instead of request body
        refresh_token = request.COOKIES.get('refresh_token')
        
        if not refresh_token:
            return Response(
                {'error': 'Refresh token not found in cookies'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Create serializer with token from cookie
        serializer = TokenRefreshSerializer(data={'refresh': refresh_token})
        
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])
        
        access_token = serializer.validated_data['access']
        
        # Return success message (token is in cookie)
        response = Response({
            'message': 'Token refreshed successfully. New access token is set as HTTP-only cookie.'
        }, status=status.HTTP_200_OK)
        
        # Set new access token as cookie
        set_access_token_cookie(response, access_token)
        
        return response


@extend_schema(
    summary="Logout user",
    description="Logout user and clear JWT cookies",
    responses={
        200: OpenApiResponse(
            description="Logout successful. Cookies cleared.",
            response={
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'}
                }
            }
        ),
        401: OpenApiResponse(description="Authentication required")
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """View for user logout - clears HTTP-only cookies."""
    response = Response({
        'message': 'Logout successful. JWT cookies have been cleared.'
    }, status=status.HTTP_200_OK)
    
    # Delete JWT cookies
    delete_jwt_cookies(response)
    
    return response

