from django.contrib import admin
from .models import Sale, SaleItem, SalePayment, Customer, Expense, DailySummary, CashDrawerSession

admin.site.register(Sale)
admin.site.register(SaleItem)
admin.site.register(SalePayment)
admin.site.register(Customer)
admin.site.register(Expense)
admin.site.register(DailySummary)
admin.site.register(CashDrawerSession)
