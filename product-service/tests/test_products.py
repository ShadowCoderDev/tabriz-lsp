"""
Unit and integration tests for Product Service.
"""
import pytest
from decimal import Decimal
from datetime import datetime
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken
from mongoengine import connect, disconnect
import mongomock
from products.models import Product


# Test database configuration
TEST_DB = 'test_product_service_db'


@pytest.fixture(scope='module')
def db_connection():
    """Setup MongoDB connection for tests."""
    # Use mongomock for testing (in-memory MongoDB)
    connect(TEST_DB, mongo_client_class=mongomock.MongoClient)
    yield
    disconnect()


@pytest.fixture(autouse=True)
def clean_database(db_connection):
    """Clean up database before each test."""
    # Clean up: delete all products before each test
    Product.objects.all().delete()
    yield
    # Clean up after test as well
    Product.objects.all().delete()


@pytest.fixture
def api_client():
    """Create API client."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, db_connection):
    """Create authenticated API client."""
    # Create a mock user for JWT token
    # Django needs a User model for JWT token generation
    from django.contrib.auth.models import User
    from django.db import transaction
    
    # Create user in SQLite (in-memory database)
    with transaction.atomic():
        user, _ = User.objects.get_or_create(
            username='testuser',
            defaults={'email': 'test@example.com'}
        )
        token = AccessToken.for_user(user)
    
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token)}')
    return api_client


@pytest.fixture
def sample_product(db_connection):
    """Create a sample product for testing."""
    import uuid
    unique_sku = f"TEST-{uuid.uuid4().hex[:8].upper()}"
    product = Product(
        name="Test Product",
        description="Test Description",
        price=Decimal('99.99'),
        stockQuantity=50,
        category="Electronics",
        sku=unique_sku,
        isActive=True
    )
    product.save()
    return product


class TestProductModel:
    """Test Product model."""
    
    def test_create_product(self, db_connection):
        """Test creating a product."""
        product = Product(
            name="New Product",
            description="New Description",
            price=Decimal('49.99'),
            stockQuantity=25,
            category="Clothing",
            sku="NEW-001"
        )
        product.save()
        
        assert product.id is not None
        assert product.name == "New Product"
        assert product.price == Decimal('49.99')
        assert product.stockQuantity == 25
        assert product.isActive is True
    
    def test_product_str(self, db_connection):
        """Test product string representation."""
        import uuid
        unique_sku = f"STR-{uuid.uuid4().hex[:8].upper()}"
        product = Product(
            name="Test Product",
            sku=unique_sku,
            price=Decimal('10.00'),
            stockQuantity=1,
            category="Test"
        )
        product.save()
        
        assert str(product) == f"Test Product ({unique_sku})"
    
    def test_product_to_dict(self, db_connection):
        """Test product to_dict method."""
        import uuid
        unique_sku = f"DICT-{uuid.uuid4().hex[:8].upper()}"
        product = Product(
            name="Test Product",
            description="Test Description",
            price=Decimal('99.99'),
            stockQuantity=50,
            category="Electronics",
            sku=unique_sku
        )
        product.save()
        
        product_dict = product.to_dict()
        assert product_dict['name'] == "Test Product"
        assert product_dict['price'] == 99.99
        assert product_dict['sku'] == unique_sku
        assert 'id' in product_dict


class TestProductAPI:
    """Test Product API endpoints."""
    
    def test_list_products_unauthenticated(self, api_client, db_connection):
        """Test that unauthenticated GET requests work (public endpoint)."""
        response = api_client.get('/api/products/')
        # GET /api/products/ is public, should return 200
        assert response.status_code == status.HTTP_200_OK
    
    def test_create_product(self, authenticated_client, db_connection):
        """Test creating a product via API."""
        data = {
            'name': 'API Test Product',
            'description': 'API Test Description',
            'price': '79.99',
            'stockQuantity': 30,
            'category': 'Electronics',
            'sku': 'API-001'
        }
        response = authenticated_client.post('/api/products/', data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'API Test Product'
        assert response.data['sku'] == 'API-001'
    
    def test_get_product(self, authenticated_client, sample_product):
        """Test retrieving a product."""
        response = authenticated_client.get(f'/api/products/{sample_product.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == sample_product.name
        assert response.data['id'] == str(sample_product.id)
    
    def test_update_product(self, authenticated_client, sample_product):
        """Test updating a product."""
        data = {
            'name': 'Updated Product',
            'description': sample_product.description,
            'price': str(sample_product.price),
            'stockQuantity': sample_product.stockQuantity,
            'category': sample_product.category,
            'sku': sample_product.sku
        }
        response = authenticated_client.put(
            f'/api/products/{sample_product.id}/',
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Updated Product'
    
    def test_delete_product(self, authenticated_client, sample_product):
        """Test soft deleting a product."""
        response = authenticated_client.delete(f'/api/products/{sample_product.id}/')
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify product is soft deleted
        product = Product.objects.get(id=sample_product.id)
        assert product.isActive is False
    
    def test_search_products(self, api_client, db_connection):
        """Test product search endpoint (public)."""
        import uuid
        # Create test products with unique SKUs
        Product(name="Laptop", description="Gaming laptop", price=Decimal('999.99'), 
                stockQuantity=10, category="Electronics", sku=f"LAP-{uuid.uuid4().hex[:8].upper()}").save()
        Product(name="Mouse", description="Wireless mouse", price=Decimal('29.99'), 
                stockQuantity=50, category="Electronics", sku=f"MOU-{uuid.uuid4().hex[:8].upper()}").save()
        
        # Search by query
        response = api_client.get('/api/products/search/', {'q': 'laptop'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) > 0
    
    def test_filter_by_category(self, authenticated_client, db_connection):
        """Test filtering products by category."""
        import uuid
        Product(name="Shirt", price=Decimal('29.99'), stockQuantity=20, 
                category="Clothing", sku=f"SHI-{uuid.uuid4().hex[:8].upper()}").save()
        Product(name="Pants", price=Decimal('49.99'), stockQuantity=15, 
                category="Clothing", sku=f"PAN-{uuid.uuid4().hex[:8].upper()}").save()
        Product(name="Phone", price=Decimal('599.99'), stockQuantity=5, 
                category="Electronics", sku=f"PHO-{uuid.uuid4().hex[:8].upper()}").save()
        
        response = authenticated_client.get('/api/products/', {'category': 'Clothing'})
        assert response.status_code == status.HTTP_200_OK
        assert all(item['category'] == 'Clothing' for item in response.data['results'])
    
    def test_filter_by_price_range(self, authenticated_client, db_connection):
        """Test filtering products by price range."""
        import uuid
        Product(name="Cheap", price=Decimal('10.00'), stockQuantity=10, 
                category="Test", sku=f"CH-{uuid.uuid4().hex[:8].upper()}").save()
        Product(name="Expensive", price=Decimal('1000.00'), stockQuantity=5, 
                category="Test", sku=f"EX-{uuid.uuid4().hex[:8].upper()}").save()
        
        response = authenticated_client.get('/api/products/', {'min_price': 50, 'max_price': 500})
        assert response.status_code == status.HTTP_200_OK
    
    def test_check_stock(self, api_client, sample_product):
        """Test product stock check endpoint."""
        response = api_client.get(f'/api/products/{sample_product.id}/stock/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['product_id'] == str(sample_product.id)
        assert response.data['stock_quantity'] == sample_product.stockQuantity
        assert response.data['in_stock'] == (sample_product.stockQuantity > 0)


class TestProductValidation:
    """Test product validation."""
    
    def test_duplicate_sku(self, authenticated_client, sample_product):
        """Test that duplicate SKU is rejected."""
        data = {
            'name': 'Another Product',
            'price': '50.00',
            'stockQuantity': 10,
            'category': 'Test',
            'sku': sample_product.sku  # Duplicate SKU
        }
        response = authenticated_client.post('/api/products/', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_negative_price(self, authenticated_client):
        """Test that negative price is rejected."""
        data = {
            'name': 'Test Product',
            'price': '-10.00',
            'stockQuantity': 10,
            'category': 'Test',
            'sku': 'TEST-002'
        }
        response = authenticated_client.post('/api/products/', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_negative_stock(self, authenticated_client):
        """Test that negative stock is rejected."""
        data = {
            'name': 'Test Product',
            'price': '10.00',
            'stockQuantity': -5,
            'category': 'Test',
            'sku': 'TEST-003'
        }
        response = authenticated_client.post('/api/products/', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
