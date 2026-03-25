from django.contrib import admin
from .models import Sale, SaleItem, Customer, Expense, DailySummary

admin.site.register(Sale)
admin.site.register(SaleItem)
admin.site.register(Customer)
admin.site.register(Expense)
admin.site.register(DailySummary)
