"""
Views for Product API.
"""
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from mongoengine.errors import DoesNotExist, ValidationError
from decimal import Decimal, InvalidOperation

from .models import Product
from .serializers import ProductSerializer, ProductListSerializer, ProductStockSerializer


class StandardResultsSetPagination(PageNumberPagination):
    """Custom pagination class."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class ProductListCreateView(generics.ListCreateAPIView):
    """
    List all products or create a new product.
    GET /api/products/ - List products with optional filtering (public)
    POST /api/products/ - Create a new product (requires authentication)
    """
    # GET is public, POST requires authentication
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]
    
    pagination_class = StandardResultsSetPagination
    serializer_class = ProductSerializer
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ProductListSerializer
        return ProductSerializer
    
    @extend_schema(
        summary="List all products",
        description="Retrieve a paginated list of products with optional filtering by category, price range, and stock availability",
        parameters=[
            OpenApiParameter(name='page', description='Page number', required=False, type=int),
            OpenApiParameter(name='page_size', description='Items per page', required=False, type=int),
            OpenApiParameter(name='category', description='Filter by category', required=False, type=str),
            OpenApiParameter(name='min_price', description='Minimum price', required=False, type=float),
            OpenApiParameter(name='max_price', description='Maximum price', required=False, type=float),
            OpenApiParameter(name='in_stock', description='Filter by stock availability', required=False, type=bool),
        ],
        responses={
            200: ProductListSerializer(many=True),
            400: OpenApiResponse(description="Bad request"),
            401: OpenApiResponse(description="Unauthorized"),
        }
    )
    def get(self, request, *args, **kwargs):
        """List products with optional filtering."""
        queryset = self.get_queryset()
        
        # Apply filters
        category = request.query_params.get('category')
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        in_stock = request.query_params.get('in_stock')
        
        if category:
            queryset = queryset.filter(category=category)
        
        if min_price:
            try:
                min_price_decimal = Decimal(str(min_price))
                queryset = queryset.filter(price__gte=min_price_decimal)
            except (ValueError, InvalidOperation):
                return Response(
                    {'error': 'Invalid min_price format'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if max_price:
            try:
                max_price_decimal = Decimal(str(max_price))
                queryset = queryset.filter(price__lte=max_price_decimal)
            except (ValueError, InvalidOperation):
                return Response(
                    {'error': 'Invalid max_price format'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if in_stock is not None:
            in_stock_bool = in_stock.lower() == 'true'
            if in_stock_bool:
                queryset = queryset.filter(stockQuantity__gt=0)
            else:
                queryset = queryset.filter(stockQuantity=0)
        
        # Only show active products by default
        queryset = queryset.filter(isActive=True)
        
        # Paginate
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def get_queryset(self):
        """Get queryset of products."""
        return Product.objects.all()
    
    @extend_schema(
        summary="Create a new product",
        description="Create a new product in the catalog",
        request=ProductSerializer,
        responses={
            201: ProductSerializer,
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Unauthorized"),
        }
    )
    def post(self, request, *args, **kwargs):
        """Create a new product."""
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            product = serializer.save()
            response_serializer = ProductSerializer(product)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a product.
    GET /api/products/{id}/ - Get product by ID (public)
    PUT /api/products/{id}/ - Full update (requires authentication)
    PATCH /api/products/{id}/ - Partial update (requires authentication)
    DELETE /api/products/{id}/ - Soft delete (requires authentication)
    """
    # GET is public, PUT/PATCH/DELETE require authentication
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]
    
    serializer_class = ProductSerializer
    lookup_field = 'id'
    
    def get_object(self):
        """Get product by ID."""
        product_id = self.kwargs.get('id')
        try:
            return Product.objects.get(id=product_id)
        except (DoesNotExist, ValidationError):
            from django.http import Http404
            raise Http404("Product not found")
    
    @extend_schema(
        summary="Get product by ID",
        description="Retrieve a specific product by its ID",
        responses={
            200: ProductSerializer,
            404: OpenApiResponse(description="Product not found"),
        }
    )
    def get(self, request, *args, **kwargs):
        """Retrieve product."""
        return self.retrieve(request, *args, **kwargs)
    
    @extend_schema(
        summary="Update product (full)",
        description="Update all fields of a product",
        request=ProductSerializer,
        responses={
            200: ProductSerializer,
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Unauthorized"),
            404: OpenApiResponse(description="Product not found"),
        }
    )
    def put(self, request, *args, **kwargs):
        """Full update."""
        return self.update(request, *args, **kwargs)
    
    @extend_schema(
        summary="Update product (partial)",
        description="Partially update a product",
        request=ProductSerializer,
        responses={
            200: ProductSerializer,
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Unauthorized"),
            404: OpenApiResponse(description="Product not found"),
        }
    )
    def patch(self, request, *args, **kwargs):
        """Partial update."""
        return self.partial_update(request, *args, **kwargs)
    
    @extend_schema(
        summary="Delete product",
        description="Soft delete a product by setting isActive=false",
        responses={
            204: OpenApiResponse(description="Product deleted successfully"),
            401: OpenApiResponse(description="Unauthorized"),
            404: OpenApiResponse(description="Product not found"),
        }
    )
    def delete(self, request, *args, **kwargs):
        """Soft delete product."""
        product = self.get_object()
        product.isActive = False
        product.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    summary="Search products",
    description="Search products by name, description, category, or other attributes",
    parameters=[
        OpenApiParameter(name='q', description='Search query (searches in name and description)', required=False, type=str),
        OpenApiParameter(name='category', description='Filter by category', required=False, type=str),
        OpenApiParameter(name='min_price', description='Minimum price', required=False, type=float),
        OpenApiParameter(name='max_price', description='Maximum price', required=False, type=float),
        OpenApiParameter(name='in_stock', description='Filter by stock availability', required=False, type=bool),
        OpenApiParameter(name='page', description='Page number', required=False, type=int),
        OpenApiParameter(name='page_size', description='Items per page', required=False, type=int),
    ],
    responses={
        200: ProductListSerializer(many=True),
        400: OpenApiResponse(description="Bad request"),
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])  # Search can be public
def product_search_view(request):
    """
    Search products by various criteria.
    GET /api/products/search/
    """
    search_query = request.query_params.get('q', '')
    category = request.query_params.get('category')
    min_price = request.query_params.get('min_price')
    max_price = request.query_params.get('max_price')
    in_stock = request.query_params.get('in_stock')
    
    # Start with active products
    queryset = Product.objects.filter(isActive=True)
    
    # Text search in name and description
    if search_query:
        queryset = queryset.filter(
            __raw__={
                '$or': [
                    {'name': {'$regex': search_query, '$options': 'i'}},
                    {'description': {'$regex': search_query, '$options': 'i'}}
                ]
            }
        )
    
    # Category filter
    if category:
        queryset = queryset.filter(category=category)
    
    # Price range filters
    if min_price:
        try:
            min_price_decimal = Decimal(str(min_price))
            queryset = queryset.filter(price__gte=min_price_decimal)
        except (ValueError, InvalidOperation):
            return Response(
                {'error': 'Invalid min_price format'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    if max_price:
        try:
            max_price_decimal = Decimal(str(max_price))
            queryset = queryset.filter(price__lte=max_price_decimal)
        except (ValueError, InvalidOperation):
            return Response(
                {'error': 'Invalid max_price format'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Stock filter
    if in_stock is not None:
        in_stock_bool = in_stock.lower() == 'true'
        if in_stock_bool:
            queryset = queryset.filter(stockQuantity__gt=0)
        else:
            queryset = queryset.filter(stockQuantity=0)
    
    # Pagination
    paginator = StandardResultsSetPagination()
    page = paginator.paginate_queryset(queryset, request)
    
    if page is not None:
        serializer = ProductListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    serializer = ProductListSerializer(queryset, many=True)
    return Response(serializer.data)


@extend_schema(
    summary="Check product stock",
    description="Get stock availability information for a product",
    responses={
        200: ProductStockSerializer,
        404: OpenApiResponse(description="Product not found"),
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])  # Stock check can be public (needed by Order Service)
def product_stock_view(request, id):
    """
    Check product stock availability.
    GET /api/products/{id}/stock/
    """
    try:
        product = Product.objects.get(id=id, isActive=True)
    except (DoesNotExist, ValidationError):
        return Response(
            {'error': 'Product not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = ProductStockSerializer({
        'product_id': str(product.id),
        'stock_quantity': product.stockQuantity,
        'in_stock': product.stockQuantity > 0,
        'available': product.isActive and product.stockQuantity > 0
    })
    
    return Response(serializer.data, status=status.HTTP_200_OK)
