"""
Product models using mongoengine for MongoDB.
"""
from mongoengine import Document, StringField, DecimalField, IntField, BooleanField, DateTimeField
from datetime import datetime
from decimal import Decimal


class Product(Document):
    """
    Product document model for MongoDB.
    """
    name = StringField(required=True, max_length=200)
    description = StringField(max_length=2000)
    price = DecimalField(required=True, precision=2, min_value=Decimal('0.00'))
    stockQuantity = IntField(required=True, min_value=0)
    category = StringField(required=True, max_length=100)
    sku = StringField(required=True, unique=True, max_length=100)
    createdAt = DateTimeField(default=datetime.utcnow)
    updatedAt = DateTimeField(default=datetime.utcnow)
    isActive = BooleanField(default=True)
    
    meta = {
        'collection': 'products',
        'indexes': [
            'sku',
            'name',
            'category',
            'price',
            'createdAt',
            ('category', 'isActive'),
            {
                'fields': ['name', 'description'],
                'default_language': 'english',
                'weights': {'name': 10, 'description': 5}
            }
        ],
        'ordering': ['-createdAt']
    }
    
    def save(self, *args, **kwargs):
        """Override save to update updatedAt timestamp."""
        self.updatedAt = datetime.utcnow()
        return super(Product, self).save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} ({self.sku})"
    
    def to_dict(self):
        """Convert document to dictionary."""
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'price': float(self.price),
            'stockQuantity': self.stockQuantity,
            'category': self.category,
            'sku': self.sku,
            'createdAt': self.createdAt.isoformat() if self.createdAt else None,
            'updatedAt': self.updatedAt.isoformat() if self.updatedAt else None,
            'isActive': self.isActive
        }
