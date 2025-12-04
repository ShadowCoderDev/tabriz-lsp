"""
Custom JWT Authentication that supports both cookie-based and header-based tokens.
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.conf import settings


class CookieJWTAuthentication(JWTAuthentication):
    """
    JWT Authentication that reads token from HTTP-only cookie.
    Falls back to Authorization header if cookie is not present.
    This allows backward compatibility with Bearer token authentication.
    """
    
    def authenticate(self, request):
        # First try to get token from cookie
        cookie_name = settings.SIMPLE_JWT.get('AUTH_COOKIE', 'access_token')
        access_token = request.COOKIES.get(cookie_name)
        
        if access_token:
            try:
                # Validate token from cookie
                validated_token = self.get_validated_token(access_token)
                user = self.get_user(validated_token)
                return (user, validated_token)
            except Exception:
                # If cookie token is invalid, try header
                pass
        
        # Fallback to Authorization header (for backward compatibility)
        header = self.get_header(request)
        if header is None:
            return None
        
        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None
        
        try:
            validated_token = self.get_validated_token(raw_token)
            user = self.get_user(validated_token)
            return (user, validated_token)
        except Exception:
            return None

