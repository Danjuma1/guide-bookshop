from django.db import models
from django.contrib.auth.models import User
from inventory.models import Product
from django.utils import timezone
import uuid


class OnlineOrder(models.Model):
    STATUS = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_METHOD = [
        ('card', 'Debit/Credit Card'),
        ('transfer', 'Bank Transfer'),
        ('pay_on_pickup', 'Pay on Pickup'),
    ]

    order_number = models.CharField(max_length=30, unique=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')

    # Customer info (for guest checkout)
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    shipping_address = models.TextField()

    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD, default='pay_on_pickup')
    payment_status = models.BooleanField(default=False)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    order_date = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.order_number

    @property
    def subtotal(self):
        return sum(item.subtotal for item in self.items.all())

    @property
    def total_amount(self):
        return self.subtotal + self.shipping_fee - self.discount_amount

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"ORD-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)


class OnlineOrderItem(models.Model):
    order = models.ForeignKey(OnlineOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def subtotal(self):
        return self.quantity * self.unit_price


class Cart(models.Model):
    session_key = models.CharField(max_length=40, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    @property
    def subtotal(self):
        return self.quantity * self.product.effective_price


class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['product', 'user']
