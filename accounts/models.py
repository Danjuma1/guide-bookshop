from django.db import models
from django.contrib.auth.models import User


class StaffProfile(models.Model):
    ROLE = [
        ('super_admin', 'Super Admin'),
        ('admin', 'Admin'),
        ('store_manager', 'Store Manager'),
        ('sales_associate', 'Sales Associate'),
        ('inventory_clerk', 'Inventory Clerk'),
        ('cashier', 'Cashier'),
    ]

    MODULES = [
        ('pos',           'Point of Sale'),
        ('sales',         'Sales History'),
        ('customers',     'Customers'),
        ('expenses',      'Expenses'),
        ('inventory',     'Products & Inventory'),
        ('reports',       'Reports & Analytics'),
        ('staff',         'Staff Management'),
        ('online_orders', 'Online Orders'),
        ('imports',       'Import Data'),
    ]

    # Default module access by role (can be overridden per-user via module_permissions)
    ROLE_DEFAULTS = {
        'super_admin': {m: True for m, _ in MODULES},
        'admin':       {m: True for m, _ in MODULES},
        'store_manager': {
            'pos': True, 'sales': True, 'customers': True, 'expenses': True,
            'inventory': True, 'reports': True, 'staff': False,
            'online_orders': True, 'imports': True,
        },
        'sales_associate': {
            'pos': True, 'sales': True, 'customers': True, 'expenses': True,
            'inventory': False, 'reports': False, 'staff': False,
            'online_orders': False, 'imports': False,
        },
        'inventory_clerk': {
            'pos': False, 'sales': False, 'customers': False, 'expenses': False,
            'inventory': True, 'reports': False, 'staff': False,
            'online_orders': False, 'imports': False,
        },
        'cashier': {
            'pos': True, 'sales': True, 'customers': False, 'expenses': False,
            'inventory': False, 'reports': False, 'staff': False,
            'online_orders': False, 'imports': False,
        },
    }

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    role = models.CharField(max_length=20, choices=ROLE, default='cashier')
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    employee_id = models.CharField(max_length=20, unique=True)
    date_joined = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    profile_pic = models.ImageField(upload_to='staff/', blank=True, null=True)
    module_permissions = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()}"

    def has_module_access(self, module):
        if self.is_admin_level or self.user.is_superuser:
            return True
        # Explicit per-user override takes priority
        if module in self.module_permissions:
            return bool(self.module_permissions[module])
        # Fall back to role defaults
        return self.ROLE_DEFAULTS.get(self.role, {}).get(module, False)

    @property
    def is_admin_level(self):
        """True for super_admin and admin roles."""
        return self.role in ('super_admin', 'admin')

    @property
    def can_write(self):
        """True if the user can create, edit, or delete records."""
        return self.role in ('super_admin', 'admin', 'store_manager') or self.user.is_superuser

    @property
    def can_view_financials(self):
        """True if the user can see cost prices, profit margins, gross/net profit."""
        return self.role in ('super_admin', 'admin') or self.user.is_superuser

    @property
    def can_view_store(self):
        """True if the user can use the View Store link."""
        return self.role == 'super_admin' or self.user.is_superuser
