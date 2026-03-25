from django.urls import path
from . import views

urlpatterns = [
    path('', views.sale_list, name='sale_list'),
    path('pos/', views.pos_view, name='pos'),
    path('new/', views.new_sale, name='new_sale'),
    path('<int:pk>/', views.sale_detail, name='sale_detail'),
    path('<int:pk>/invoice/', views.sale_invoice, name='sale_invoice'),
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/add/', views.customer_add, name='customer_add'),
    path('customers/<int:pk>/', views.customer_detail, name='customer_detail'),
    path('customers/<int:pk>/edit/', views.customer_edit, name='customer_edit'),
    path('customers/<int:pk>/delete/', views.customer_delete, name='customer_delete'),
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/add/', views.expense_add, name='expense_add'),
    path('expenses/<int:pk>/edit/', views.expense_edit, name='expense_edit'),
    path('expenses/<int:pk>/delete/', views.expense_delete, name='expense_delete'),
    path('reports/', views.reports_view, name='reports'),
    path('api/product-search/', views.product_search_api, name='product_search_api'),
    path('api/process-sale/', views.process_sale_api, name='process_sale_api'),
    path('import/customers/', views.import_customers, name='import_customers'),
    path('<int:pk>/receipt/', views.sale_receipt, name='sale_receipt'),
]
