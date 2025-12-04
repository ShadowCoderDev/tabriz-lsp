"""
Prometheus metrics for Product Service.
"""
from prometheus_client import Counter, Histogram, Gauge
from django.utils.deprecation import MiddlewareMixin
import time

# HTTP metrics
http_requests_total = Counter(
    'product_service_http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'product_service_http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# Product metrics
products_total = Gauge(
    'product_service_products_total',
    'Total number of products in catalog'
)

products_by_category = Gauge(
    'product_service_products_by_category',
    'Number of products by category',
    ['category']
)

products_low_stock = Gauge(
    'product_service_products_low_stock',
    'Number of products with low stock (stockQuantity < 10)'
)


class PrometheusMiddleware(MiddlewareMixin):
    """
    Middleware to collect Prometheus metrics.
    """
    
    def process_request(self, request):
        """Store request start time."""
        request._prometheus_start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """Record metrics for the request."""
        if hasattr(request, '_prometheus_start_time'):
            duration = time.time() - request._prometheus_start_time
            
            # Extract endpoint (simplified)
            endpoint = request.path
            if len(endpoint) > 50:  # Truncate long paths
                endpoint = endpoint[:50]
            
            # Record metrics
            http_requests_total.labels(
                method=request.method,
                endpoint=endpoint,
                status=response.status_code
            ).inc()
            
            http_request_duration_seconds.labels(
                method=request.method,
                endpoint=endpoint
            ).observe(duration)
        
        return response
