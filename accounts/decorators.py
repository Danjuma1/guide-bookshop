from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

_MODULE_URLS = {
    'pos': 'pos',
    'sales': 'sale_list',
    'customers': 'customer_list',
    'expenses': 'expense_list',
    'inventory': 'product_list',
    'reports': 'reports',
    'staff': 'staff_list',
    'online_orders': 'manage_orders',
    'imports': 'import_products',
}


def _first_accessible_url(user):
    try:
        profile = user.staff_profile
        for key, url_name in _MODULE_URLS.items():
            if profile.has_module_access(key):
                return url_name
    except Exception:
        pass
    return 'profile'


def admin_required(view_func):
    """Restrict a view to admin-level users (admin or super_admin) only."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        try:
            if request.user.staff_profile.is_admin_level:
                return view_func(request, *args, **kwargs)
        except Exception:
            pass
        messages.error(request, "The dashboard is only accessible to admins.")
        return redirect(_first_accessible_url(request.user))
    return wrapper


def module_required(module):
    """Restrict a view to staff who have access to the given module."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            try:
                if not request.user.staff_profile.has_module_access(module):
                    messages.error(request, "You don't have permission to access that module.")
                    return redirect(_first_accessible_url(request.user))
            except Exception:
                pass
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def write_required(view_func):
    """Restrict write/CRUD operations to users with write permission."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        try:
            if request.user.staff_profile.can_write:
                return view_func(request, *args, **kwargs)
        except Exception:
            pass
        messages.error(request, "You don't have permission to perform this action.")
        return redirect(_first_accessible_url(request.user))
    return wrapper
