"""
Utility functions for managing JWT cookies.
"""
from django.conf import settings
from rest_framework.response import Response


def set_jwt_cookies(response, access_token, refresh_token):
    """
    Set JWT tokens as HTTP-only cookies in the response.
    
    Args:
        response: Django HttpResponse or DRF Response object
        access_token: JWT access token string
        refresh_token: JWT refresh token string
    
    Returns:
        Response object with cookies set
    """
    # Get token lifetimes from settings
    access_lifetime = settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']
    refresh_lifetime = settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME']
    
    # Calculate max_age in seconds
    access_max_age = int(access_lifetime.total_seconds())
    refresh_max_age = int(refresh_lifetime.total_seconds())
    
    # Cookie settings
    cookie_settings = {
        'httponly': True,  # Prevent JavaScript access
        'samesite': 'Lax',  # CSRF protection
        'secure': not settings.DEBUG,  # Only HTTPS in production
        'path': '/',
    }
    
    # Set access token cookie
    response.set_cookie(
        key='access_token',
        value=access_token,
        max_age=access_max_age,
        **cookie_settings
    )
    
    # Set refresh token cookie
    response.set_cookie(
        key='refresh_token',
        value=refresh_token,
        max_age=refresh_max_age,
        **cookie_settings
    )
    
    return response


def delete_jwt_cookies(response):
    """
    Delete JWT cookies from response.
    
    Args:
        response: Django HttpResponse or DRF Response object
    
    Returns:
        Response object with cookies deleted
    """
    cookie_settings = {
        'path': '/',
        'samesite': 'Lax',
    }
    
    response.delete_cookie('access_token', **cookie_settings)
    response.delete_cookie('refresh_token', **cookie_settings)
    
    return response


def set_access_token_cookie(response, access_token):
    """
    Set only access token as HTTP-only cookie.
    Used for token refresh.
    
    Args:
        response: Django HttpResponse or DRF Response object
        access_token: JWT access token string
    
    Returns:
        Response object with cookie set
    """
    access_lifetime = settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']
    access_max_age = int(access_lifetime.total_seconds())
    
    response.set_cookie(
        key='access_token',
        value=access_token,
        max_age=access_max_age,
        httponly=True,
        samesite='Lax',
        secure=not settings.DEBUG,
        path='/',
    )
    
    return response

