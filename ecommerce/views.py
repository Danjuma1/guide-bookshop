from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.conf import settings as django_settings
from django.template.loader import render_to_string
from inventory.models import Product, Category
from core.models import SiteSettings
from .models import Cart, CartItem, OnlineOrder, OnlineOrderItem
from accounts.decorators import module_required


def get_or_create_cart(request):
    if not request.session.session_key:
        request.session.create()
    cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
    return cart


def shop_home(request):
    products = Product.objects.filter(is_active=True, is_available_online=True)
    categories = Category.objects.all()
    q = request.GET.get('q', '')
    category_slug = request.GET.get('category', '')
    product_type = request.GET.get('type', '')
    sort = request.GET.get('sort', '')

    if q:
        products = products.filter(Q(name__icontains=q) | Q(author__icontains=q) | Q(description__icontains=q))
    if category_slug:
        products = products.filter(category__slug=category_slug)
    if product_type:
        products = products.filter(product_type=product_type)
    if sort == 'price_asc':
        products = products.order_by('selling_price')
    elif sort == 'price_desc':
        products = products.order_by('-selling_price')
    elif sort == 'newest':
        products = products.order_by('-created_at')
    else:
        products = products.order_by('name')

    paginator = Paginator(products, 24)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'ecommerce/shop.html', {
        'products': page_obj, 'page_obj': page_obj, 'categories': categories,
        'q': q, 'selected_category': category_slug,
        'selected_type': product_type, 'sort': sort,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True, is_available_online=True)
    related = Product.objects.filter(
        category=product.category, is_active=True, is_available_online=True
    ).exclude(pk=product.pk)[:4]
    reviews = product.reviews.select_related('user').order_by('-created_at')
    return render(request, 'ecommerce/product_detail.html', {
        'product': product, 'related': related, 'reviews': reviews,
    })


def category_products(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(
        category=category, is_active=True, is_available_online=True
    )
    return render(request, 'ecommerce/shop.html', {
        'products': products, 'current_category': category,
        'categories': Category.objects.all(),
    })


def cart_view(request):
    cart = get_or_create_cart(request)
    items = cart.items.select_related('product').all()
    total = sum(item.subtotal for item in items)
    return render(request, 'ecommerce/cart.html', {'cart': cart, 'items': items, 'total': total})


@require_POST
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True, is_available_online=True)
    if product.quantity_in_stock < 1:
        messages.error(request, f'"{product.name}" is out of stock.')
        return redirect(request.META.get('HTTP_REFERER', 'shop_home'))
    cart = get_or_create_cart(request)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        if item.quantity >= product.quantity_in_stock:
            messages.error(request, f'Only {product.quantity_in_stock} unit(s) available.')
            return redirect(request.META.get('HTTP_REFERER', 'cart'))
        item.quantity += 1
        item.save()
    messages.success(request, f'"{product.name}" added to cart.')
    return redirect(request.META.get('HTTP_REFERER', 'cart'))


@require_POST
def update_cart(request, item_id):
    cart = get_or_create_cart(request)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    try:
        qty = int(request.POST.get('quantity', 1))
    except (ValueError, TypeError):
        qty = 1
    if qty < 1:
        item.delete()
    elif qty > item.product.quantity_in_stock:
        messages.error(request, f'Only {item.product.quantity_in_stock} unit(s) available.')
        item.quantity = item.product.quantity_in_stock
        item.save()
    else:
        item.quantity = qty
        item.save()
    return redirect('cart')


@require_POST
def remove_from_cart(request, item_id):
    cart = get_or_create_cart(request)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    item.delete()
    messages.success(request, 'Item removed from cart.')
    return redirect('cart')


def checkout(request):
    cart = get_or_create_cart(request)
    items = cart.items.select_related('product').all()

    if not items:
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart')

    total = sum(item.subtotal for item in items)
    site_settings = SiteSettings.objects.first()

    if request.method == 'POST':
        customer_name = request.POST.get('customer_name', '').strip()
        customer_email = request.POST.get('customer_email', '').strip()
        customer_phone = request.POST.get('customer_phone', '').strip()
        shipping_address = request.POST.get('shipping_address', '').strip()
        payment_method = request.POST.get('payment_method', 'pay_on_pickup')
        notes = request.POST.get('notes', '').strip()

        # Input validation
        if not all([customer_name, customer_email, customer_phone, shipping_address]):
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'ecommerce/checkout.html', {'cart': cart, 'items': items, 'total': total})

        if len(customer_name) > 200 or len(customer_phone) > 20 or len(shipping_address) > 500:
            messages.error(request, 'One or more fields exceed the allowed length.')
            return render(request, 'ecommerce/checkout.html', {'cart': cart, 'items': items, 'total': total})

        try:
            validate_email(customer_email)
        except ValidationError:
            messages.error(request, 'Please enter a valid email address.')
            return render(request, 'ecommerce/checkout.html', {'cart': cart, 'items': items, 'total': total})

        valid_payment_methods = [m for m, _ in OnlineOrder.PAYMENT_METHOD]
        if payment_method not in valid_payment_methods:
            payment_method = 'pay_on_pickup'

        # Validate stock availability before creating the order
        for item in items:
            if not item.product.is_active or not item.product.is_available_online:
                messages.error(request, f'"{item.product.name}" is no longer available.')
                return redirect('cart')
            if item.product.quantity_in_stock < item.quantity:
                messages.error(request, f'"{item.product.name}" only has {item.product.quantity_in_stock} unit(s) left.')
                return redirect('cart')

        order = OnlineOrder.objects.create(
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            shipping_address=shipping_address,
            payment_method=payment_method,
            notes=notes[:1000],
            user=request.user if request.user.is_authenticated else None,
        )
        for item in items:
            OnlineOrderItem.objects.create(
                order=order, product=item.product,
                quantity=item.quantity,
                unit_price=item.product.effective_price,
            )
        cart.items.all().delete()
        # Allow guest to view their own order via session
        placed = request.session.get('placed_orders', [])
        placed.append(order.order_number)
        request.session['placed_orders'] = placed[-10:]  # keep last 10 max

        # Notify admin by email
        _send_order_notification(order, site_settings)

        messages.success(request, f'Order {order.order_number} placed successfully! We will contact you shortly.')
        return redirect('order_detail', order_number=order.order_number)

    return render(request, 'ecommerce/checkout.html', {
        'cart': cart, 'items': items, 'total': total, 'site_settings': site_settings,
    })


def _send_order_notification(order, site_settings):
    admin_email = getattr(django_settings, 'ADMIN_EMAIL', '')
    if site_settings and site_settings.email:
        admin_email = admin_email or site_settings.email
    if not admin_email:
        return
    try:
        item_lines = '\n'.join(
            f"  - {item.product.name} x{item.quantity} @ ₦{item.unit_price} = ₦{item.subtotal}"
            for item in order.items.select_related('product')
        )
        body = (
            f"New online order received!\n\n"
            f"Order Number : {order.order_number}\n"
            f"Date         : {order.order_date.strftime('%d %b %Y, %H:%M')}\n\n"
            f"--- Customer ---\n"
            f"Name    : {order.customer_name}\n"
            f"Email   : {order.customer_email}\n"
            f"Phone   : {order.customer_phone}\n"
            f"Address : {order.shipping_address}\n\n"
            f"--- Items ---\n{item_lines}\n\n"
            f"Payment Method : {order.get_payment_method_display()}\n"
            f"Order Total    : ₦{order.total_amount}\n"
            f"\nLog in to the admin panel to manage this order."
        )
        send_mail(
            subject=f"New Order {order.order_number} – {order.customer_name}",
            message=body,
            from_email=django_settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin_email],
            fail_silently=True,
        )
    except Exception:
        pass


def order_detail(request, order_number):
    order = get_object_or_404(OnlineOrder, order_number=order_number)
    # Authenticated staff can view any order; guests/customers only their own session's order
    if request.user.is_authenticated and hasattr(request.user, 'staff_profile'):
        pass  # staff access allowed
    elif request.user.is_authenticated:
        if order.user != request.user:
            messages.error(request, 'You do not have permission to view this order.')
            return redirect('order_list')
    else:
        # Guest: only allow if order_number was just placed (stored in session)
        allowed = request.session.get('placed_orders', [])
        if order_number not in allowed:
            messages.error(request, 'Order not found or access denied.')
            return redirect('shop_home')
    site_settings = SiteSettings.objects.first()
    return render(request, 'ecommerce/order_detail.html', {'order': order, 'site_settings': site_settings})


def order_list(request):
    if request.user.is_authenticated:
        orders = OnlineOrder.objects.filter(user=request.user).order_by('-order_date')
    else:
        orders = []
    return render(request, 'ecommerce/order_list.html', {'orders': orders})


@login_required
@module_required('online_orders')
def manage_orders(request):
    orders = OnlineOrder.objects.all().order_by('-order_date')
    status = request.GET.get('status', '')
    if status:
        orders = orders.filter(status=status)
    return render(request, 'ecommerce/manage_orders.html', {'orders': orders, 'status': status})


@login_required
@module_required('online_orders')
def admin_order_detail(request, pk):
    order = get_object_or_404(OnlineOrder, pk=pk)
    return render(request, 'ecommerce/admin_order_detail.html', {'order': order})


# Statuses at which the order's stock is considered committed (deducted).
_STOCK_COMMITTED_STATUSES = {'confirmed', 'processing', 'shipped', 'delivered'}


def _deduct_order_stock(order, user):
    """Decrement stock for each order item and log the movement. Idempotent
    via order.stock_deducted."""
    from inventory.models import StockMovement
    for item in order.items.select_related('product'):
        product = item.product
        prev = product.quantity_in_stock
        product.quantity_in_stock = max(0, product.quantity_in_stock - item.quantity)
        product.save(update_fields=['quantity_in_stock', 'updated_at'])
        StockMovement.objects.create(
            product=product, movement_type='out',
            quantity=item.quantity, previous_stock=prev,
            new_stock=product.quantity_in_stock,
            reference=order.order_number,
            notes='Online order confirmed',
            created_by=user,
        )
    order.stock_deducted = True


def _restore_order_stock(order, user):
    """Return stock previously deducted for an order (e.g. on cancellation)."""
    from inventory.models import StockMovement
    for item in order.items.select_related('product'):
        product = item.product
        prev = product.quantity_in_stock
        product.quantity_in_stock += item.quantity
        product.save(update_fields=['quantity_in_stock', 'updated_at'])
        StockMovement.objects.create(
            product=product, movement_type='return',
            quantity=item.quantity, previous_stock=prev,
            new_stock=product.quantity_in_stock,
            reference=f'CANCEL-{order.order_number}',
            notes='Online order cancelled',
            created_by=user,
        )
    order.stock_deducted = False


def _record_order_sale(order, user):
    """Create a completed Sale mirroring a delivered online order so it flows
    into all sales reporting. Stock is NOT touched here (already deducted at
    confirmation). Idempotent via order.recorded_sale."""
    from django.utils import timezone
    from sales.models import Sale, SaleItem, SalePayment
    sale = Sale.objects.create(
        served_by=user,
        payment_method='online',
        discount_amount=order.discount_amount,
        status='completed',
        payment_status=True,
        sale_date=timezone.now(),
        notes=f'Online order {order.order_number}',
    )
    for item in order.items.select_related('product'):
        SaleItem.objects.create(
            sale=sale, product=item.product,
            quantity=item.quantity,
            unit_price=item.unit_price,
            unit_cost=item.product.cost_price,
        )
    SalePayment.objects.create(sale=sale, method='online', amount=sale.total_amount)
    order.recorded_sale = sale


@login_required
@module_required('online_orders')
def update_order_status(request, pk):
    order = get_object_or_404(OnlineOrder, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(OnlineOrder.STATUS) and new_status != order.status:
            order.status = new_status

            # Reserve stock the first time the order is committed.
            if new_status in _STOCK_COMMITTED_STATUSES and not order.stock_deducted:
                _deduct_order_stock(order, request.user)

            # Recognise the sale once delivered.
            if new_status == 'delivered' and order.recorded_sale is None:
                _record_order_sale(order, request.user)

            # On cancellation, undo stock and void any recorded sale.
            if new_status == 'cancelled':
                if order.stock_deducted:
                    _restore_order_stock(order, request.user)
                if order.recorded_sale is not None:
                    sale = order.recorded_sale
                    sale.status = 'cancelled'
                    sale.save(update_fields=['status', 'updated_at'])

            order.save()
            messages.success(request, f'Order {order.order_number} status updated.')
        else:
            messages.info(request, 'Order status unchanged.')
    next_url = request.POST.get('next', '')
    if next_url == 'detail':
        return redirect('admin_order_detail', pk=pk)
    return redirect('manage_orders')
