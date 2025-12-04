"""
Custom exception handlers for Product Service.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from mongoengine.errors import ValidationError, NotUniqueError
from django.http import Http404


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides consistent error responses.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Customize the response data structure
        custom_response_data = {
            'error': 'An error occurred',
            'details': response.data
        }
        response.data = custom_response_data
        return response
    
    # Handle mongoengine-specific exceptions
    if isinstance(exc, ValidationError):
        return Response(
            {
                'error': 'Validation error',
                'details': str(exc)
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if isinstance(exc, NotUniqueError):
        return Response(
            {
                'error': 'Duplicate entry',
                'details': 'A product with this SKU already exists.'
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if isinstance(exc, Http404):
        return Response(
            {
                'error': 'Not found',
                'details': 'The requested resource was not found.'
            },
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Handle unexpected errors
    return Response(
        {
            'error': 'Internal server error',
            'details': str(exc) if str(exc) else 'An unexpected error occurred.'
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
