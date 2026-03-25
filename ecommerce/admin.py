from django.contrib import admin
from .models import OnlineOrder, OnlineOrderItem, Cart, CartItem, ProductReview
admin.site.register(OnlineOrder)
admin.site.register(OnlineOrderItem)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(ProductReview)
