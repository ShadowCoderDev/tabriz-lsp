"""
URL configuration for products app.
"""
from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Product CRUD
    path('', views.ProductListCreateView.as_view(), name='product-list-create'),
    path('<str:id>/', views.ProductDetailView.as_view(), name='product-detail'),
    
    # Product search
    path('search/', views.product_search_view, name='product-search'),
    
    # Product stock check
    path('<str:id>/stock/', views.product_stock_view, name='product-stock'),
]
