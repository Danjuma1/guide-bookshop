from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
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


def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    cart = get_or_create_cart(request)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity += 1
        item.save()
    messages.success(request, f'"{product.name}" added to cart.')
    return redirect(request.META.get('HTTP_REFERER', 'cart'))


def update_cart(request, item_id):
    cart = get_or_create_cart(request)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    qty = int(request.POST.get('quantity', 1))
    if qty > 0:
        item.quantity = qty
        item.save()
    else:
        item.delete()
    return redirect('cart')


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
        # Validate stock availability before creating the order
        for item in items:
            if not item.product.is_available_online or item.product.quantity_in_stock < item.quantity:
                messages.error(request, f'"{item.product.name}" is no longer available in the requested quantity.')
                return redirect('cart')

        order = OnlineOrder.objects.create(
            customer_name=request.POST.get('customer_name'),
            customer_email=request.POST.get('customer_email'),
            customer_phone=request.POST.get('customer_phone'),
            shipping_address=request.POST.get('shipping_address'),
            payment_method=request.POST.get('payment_method', 'pay_on_pickup'),
            notes=request.POST.get('notes', ''),
            user=request.user if request.user.is_authenticated else None,
        )
        for item in items:
            OnlineOrderItem.objects.create(
                order=order, product=item.product,
                quantity=item.quantity,
                unit_price=item.product.effective_price,
            )
        cart.items.all().delete()
        messages.success(request, f'Order {order.order_number} placed successfully! We will contact you shortly.')
        return redirect('order_detail', order_number=order.order_number)

    return render(request, 'ecommerce/checkout.html', {'cart': cart, 'items': items, 'total': total})


def order_detail(request, order_number):
    order = get_object_or_404(OnlineOrder, order_number=order_number)
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
