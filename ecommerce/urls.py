from django.urls import path
from . import views

urlpatterns = [
    path('', views.shop_home, name='shop_home'),
    path('product/<slug:slug>/', views.product_detail, name='shop_product_detail'),
    path('category/<slug:slug>/', views.category_products, name='category_products'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('orders/', views.order_list, name='order_list'),
    path('orders/manage/', views.manage_orders, name='manage_orders'),  # MUST be before <str:order_number>
    path('orders/<int:pk>/update-status/', views.update_order_status, name='update_order_status'),
    path('orders/<str:order_number>/', views.order_detail, name='order_detail'),
]
