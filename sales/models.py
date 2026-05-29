from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from inventory.models import Product
import uuid


class Customer(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    is_walk_in = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    @property
    def total_purchases(self):
        return self.sales.filter(status='completed').count()


class Sale(models.Model):
    STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    PAYMENT_METHOD = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('transfer', 'Bank Transfer'),
        ('pos', 'POS'),
        ('online', 'Online Payment'),
        ('split', 'Split Payment'),
    ]

    # Methods a single payment line can use (excludes the composite 'split')
    PAYMENT_LINE_METHOD = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('transfer', 'Bank Transfer'),
        ('pos', 'POS'),
        ('online', 'Online Payment'),
    ]

    invoice_number = models.CharField(max_length=20, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales')
    served_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD, default='cash')
    payment_status = models.BooleanField(default=False)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    sale_date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.invoice_number

    @property
    def subtotal(self):
        return sum(item.subtotal for item in self.items.all())

    @property
    def total_amount(self):
        return self.subtotal - self.discount_amount

    @property
    def total_profit(self):
        return sum(item.profit for item in self.items.all())

    @property
    def payment_list(self):
        """List of (method, amount) tuples. Falls back to the single
        payment_method/total for legacy sales that have no payment rows."""
        pays = list(self.payments.all())
        if pays:
            return [(p.method, p.amount) for p in pays]
        return [(self.payment_method, self.total_amount)]

    @property
    def is_split(self):
        return self.payments.count() > 1

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = f"INV-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
        super().save(*args, **kwargs)


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    @property
    def subtotal(self):
        return self.quantity * self.unit_price

    @property
    def profit(self):
        return (self.unit_price - self.unit_cost) * self.quantity


class SalePayment(models.Model):
    """A single payment line against a sale. A sale can have several of these
    (split payment), e.g. part cash + part bank transfer."""
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='payments')
    method = models.CharField(max_length=20, choices=Sale.PAYMENT_LINE_METHOD, default='cash')
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sale.invoice_number} - {self.get_method_display()} ₦{self.amount}"


class Expense(models.Model):
    CATEGORY = [
        ('rent', 'Rent'),
        ('utilities', 'Utilities'),
        ('salary', 'Salary'),
        ('supplies', 'Office Supplies'),
        ('maintenance', 'Maintenance'),
        ('marketing', 'Marketing'),
        ('transport', 'Transport'),
        ('other', 'Other'),
    ]

    title = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY, default='other')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    expense_date = models.DateField(default=timezone.now)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - ₦{self.amount}"


class DailySummary(models.Model):
    date = models.DateField(unique=True)
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_transactions = models.IntegerField(default=0)
    total_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cash_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    card_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    transfer_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    pos_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    online_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    closed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    is_closed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class CashDrawerSession(models.Model):
    """Per-cashier, per-day cash reconciliation.

    Tracks the cash a cashier starts the day with (balance brought forward),
    the cash they accumulate from sales, how much they transfer to the bank at
    closing, and the cash they carry forward to the next day.
    """
    cashier = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cash_sessions')
    date = models.DateField(default=timezone.localdate)
    opening_float = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cash_transferred_to_bank = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    closing_float = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    counted_cash = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    is_closed = models.BooleanField(default=False)
    closed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('cashier', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.cashier} — {self.date}"

    @property
    def cash_sales(self):
        """Cash collected by this cashier from completed sales on this date."""
        from decimal import Decimal
        total = Decimal('0')
        sales = Sale.objects.filter(
            served_by=self.cashier,
            status='completed',
            sale_date__date=self.date,
        ).prefetch_related('payments')
        for s in sales:
            for method, amount in s.payment_list:
                if method == 'cash':
                    total += Decimal(str(amount))
        return total

    @property
    def expected_cash(self):
        """Cash that should be in the drawer at end of day before any transfer."""
        return self.opening_float + self.cash_sales

    @property
    def variance(self):
        """Counted cash minus expected (only meaningful once counted)."""
        return self.counted_cash - self.expected_cash
