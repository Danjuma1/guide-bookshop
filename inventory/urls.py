from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('add/', views.product_add, name='product_add'),
    path('<int:pk>/', views.product_detail, name='product_detail'),
    path('<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.category_add, name='category_add'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/add/', views.supplier_add, name='supplier_add'),
    path('suppliers/<int:pk>/', views.supplier_detail, name='supplier_detail'),
    path('suppliers/<int:pk>/edit/', views.supplier_edit, name='supplier_edit'),
    path('suppliers/<int:pk>/delete/', views.supplier_delete, name='supplier_delete'),
    path('stock-movement/', views.stock_movement_list, name='stock_movement_list'),
    path('adjust-stock/<int:pk>/', views.adjust_stock, name='adjust_stock'),
    path('purchase-orders/', views.po_list, name='po_list'),
    path('purchase-orders/add/', views.po_add, name='po_add'),
    path('purchase-orders/<int:pk>/', views.po_detail, name='po_detail'),
    path('low-stock/', views.low_stock_report, name='low_stock_report'),
    path('import/products/', views.import_products, name='import_products'),
    path('import/suppliers/', views.import_suppliers, name='import_suppliers'),
]
