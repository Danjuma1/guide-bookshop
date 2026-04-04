from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from inventory.models import Product, Category
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

    return render(request, 'ecommerce/shop.html', {
        'products': products, 'categories': categories,
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
        messages.success(request, f'Order {order.order_number} placed successfully! We will contact you shortly.')
        return redirect('order_detail', order_number=order.order_number)

    return render(request, 'ecommerce/checkout.html', {'cart': cart, 'items': items, 'total': total})


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
    return render(request, 'ecommerce/order_detail.html', {'order': order})


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
def update_order_status(request, pk):
    order = get_object_or_404(OnlineOrder, pk=pk)
    if request.method == 'POST':
        order.status = request.POST.get('status')
        order.save()
        messages.success(request, f'Order {order.order_number} status updated.')
    return redirect('manage_orders')
