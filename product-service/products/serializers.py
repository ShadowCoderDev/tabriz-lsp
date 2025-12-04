"""
Serializers for Product API.
"""
from rest_framework import serializers
from decimal import Decimal, InvalidOperation
from .models import Product


class ProductSerializer(serializers.Serializer):
    """Serializer for Product model."""
    
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(max_length=200, required=True)
    description = serializers.CharField(max_length=2000, required=False, allow_blank=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.00'), required=True)
    stockQuantity = serializers.IntegerField(min_value=0, required=True)
    category = serializers.CharField(max_length=100, required=True)
    sku = serializers.CharField(max_length=100, required=True)
    createdAt = serializers.DateTimeField(read_only=True)
    updatedAt = serializers.DateTimeField(read_only=True)
    isActive = serializers.BooleanField(default=True, required=False)
    
    def validate_sku(self, value):
        """Validate SKU uniqueness."""
        if self.instance:
            # Update: check if SKU is taken by another product
            existing = Product.objects(sku=value, id__ne=self.instance.id).first()
        else:
            # Create: check if SKU already exists
            existing = Product.objects(sku=value).first()
        
        if existing:
            raise serializers.ValidationError("A product with this SKU already exists.")
        return value
    
    def validate_name(self, value):
        """Validate product name."""
        if not value or not value.strip():
            raise serializers.ValidationError("Product name cannot be empty.")
        return value.strip()
    
    def validate_price(self, value):
        """Validate price."""
        try:
            price = Decimal(str(value))
            if price < 0:
                raise serializers.ValidationError("Price cannot be negative.")
            return price
        except (InvalidOperation, ValueError):
            raise serializers.ValidationError("Invalid price format.")
    
    def create(self, validated_data):
        """Create a new product."""
        return Product.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        """Update an existing product."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class ProductListSerializer(serializers.Serializer):
    """Simplified serializer for product list views."""
    
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    price = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)
    stockQuantity = serializers.IntegerField(read_only=True)
    category = serializers.CharField(read_only=True)
    sku = serializers.CharField(read_only=True)
    isActive = serializers.BooleanField(read_only=True)


class ProductStockSerializer(serializers.Serializer):
    """Serializer for product stock information."""
    
    product_id = serializers.CharField(read_only=True)
    stock_quantity = serializers.IntegerField(read_only=True)
    in_stock = serializers.BooleanField(read_only=True)
    available = serializers.BooleanField(read_only=True)
