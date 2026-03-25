from django.contrib import admin
from .models import Product, Category, Supplier, StockMovement, PurchaseOrder, PurchaseOrderItem

admin.site.register(Product)
admin.site.register(Category)
admin.site.register(Supplier)
admin.site.register(StockMovement)
admin.site.register(PurchaseOrder)
admin.site.register(PurchaseOrderItem)
