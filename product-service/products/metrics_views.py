"""
Prometheus metrics endpoint.
"""
from django.http import HttpResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny


@api_view(['GET'])
@permission_classes([AllowAny])
def metrics_view(request):
    """
    Prometheus metrics endpoint.
    GET /metrics/
    """
    metrics = generate_latest()
    return HttpResponse(metrics, content_type=CONTENT_TYPE_LATEST)
