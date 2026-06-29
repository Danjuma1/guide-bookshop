from django.contrib import admin
from .models import Sale, SaleItem, SalePayment, Customer, Expense, DailySummary, CashDrawerSession, CreditAccount, CreditTransaction, CreditTransactionItem

admin.site.register(Sale)
admin.site.register(SaleItem)
admin.site.register(SalePayment)
admin.site.register(Customer)
admin.site.register(Expense)
admin.site.register(DailySummary)
admin.site.register(CashDrawerSession)
admin.site.register(CreditAccount)
admin.site.register(CreditTransaction)
admin.site.register(CreditTransactionItem)
