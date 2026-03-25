from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class Supplier(models.Model):
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    PRODUCT_TYPE = [
        ('book', 'Book'),
        ('stationery', 'Stationery'),
        ('art_supply', 'Art Supply'),
        ('educational', 'Educational Material'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    sku = models.CharField(max_length=50, unique=True)
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPE, default='book')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)

    # Book-specific fields
    author = models.CharField(max_length=200, blank=True)
    isbn = models.CharField(max_length=20, blank=True)
    publisher = models.CharField(max_length=200, blank=True)
    edition = models.CharField(max_length=50, blank=True)

    # Pricing
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Stock
    quantity_in_stock = models.IntegerField(default=0)
    reorder_level = models.IntegerField(default=5)
    reorder_quantity = models.IntegerField(default=20)

    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_available_online = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def effective_price(self):
        if self.discount_price:
            return self.discount_price
        return self.selling_price

    @property
    def is_low_stock(self):
        return self.quantity_in_stock <= self.reorder_level

    @property
    def profit_margin(self):
        if self.cost_price > 0:
            return ((self.selling_price - self.cost_price) / self.cost_price) * 100
        return 0


class StockMovement(models.Model):
    MOVEMENT_TYPE = [
        ('in', 'Stock In'),
        ('out', 'Stock Out'),
        ('adjustment', 'Adjustment'),
        ('return', 'Return'),
        ('damage', 'Damage/Loss'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPE)
    quantity = models.IntegerField()
    previous_stock = models.IntegerField()
    new_stock = models.IntegerField()
    reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.movement_type} ({self.quantity})"


class PurchaseOrder(models.Model):
    STATUS = [
        ('draft', 'Draft'),
        ('sent', 'Sent to Supplier'),
        ('partial', 'Partially Received'),
        ('received', 'Fully Received'),
        ('cancelled', 'Cancelled'),
    ]

    po_number = models.CharField(max_length=20, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS, default='draft')
    order_date = models.DateField(default=timezone.now)
    expected_date = models.DateField(null=True, blank=True)
    received_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.po_number

    @property
    def total_amount(self):
        return sum(item.subtotal for item in self.items.all())


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity_ordered = models.IntegerField()
    quantity_received = models.IntegerField(default=0)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def subtotal(self):
        return self.quantity_ordered * self.unit_cost
