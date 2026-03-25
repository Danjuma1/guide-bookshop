from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import timedelta, date
from inventory.models import Product, Category
from sales.models import Sale, SaleItem
from ecommerce.models import OnlineOrder
from .models import Banner
from accounts.decorators import admin_required


def landing_page(request):
    featured_products = Product.objects.filter(is_featured=True, is_active=True, is_available_online=True)[:8]
    categories = Category.objects.filter(parent=None)[:8]
    banners = Banner.objects.filter(is_active=True)[:3]
    new_arrivals = Product.objects.filter(is_active=True, is_available_online=True).order_by('-created_at')[:8]
    return render(request, 'core/landing.html', {
        'featured_products': featured_products,
        'categories': categories,
        'banners': banners,
        'new_arrivals': new_arrivals,
    })


def about_page(request):
    return render(request, 'core/about.html')


def contact_page(request):
    return render(request, 'core/contact.html')


@login_required
@admin_required
def dashboard(request):
    today = date.today()
    month_start = today.replace(day=1)

    today_sales = Sale.objects.filter(sale_date__date=today, status='completed')
    today_revenue = sum(s.total_amount for s in today_sales)
    today_transactions = today_sales.count()

    monthly_sales = Sale.objects.filter(sale_date__date__gte=month_start, status='completed')
    monthly_revenue = sum(s.total_amount for s in monthly_sales)
    monthly_transactions = monthly_sales.count()

    low_stock_count = Product.objects.filter(
        quantity_in_stock__lte=F('reorder_level'), is_active=True
    ).count()
    out_of_stock = Product.objects.filter(quantity_in_stock=0, is_active=True).count()

    recent_sales = Sale.objects.filter(status='completed').order_by('-sale_date')[:8]
    pending_online_orders = OnlineOrder.objects.filter(status__in=['pending', 'confirmed']).count()

    chart_data = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        day_rev = sum(s.total_amount for s in Sale.objects.filter(sale_date__date=d, status='completed'))
        chart_data.append({'date': d.strftime('%d %b'), 'revenue': float(day_rev)})

    top_products = SaleItem.objects.filter(
        sale__sale_date__date__gte=month_start, sale__status='completed'
    ).values('product__name').annotate(total_qty=Sum('quantity')).order_by('-total_qty')[:5]

    context = {
        'today_revenue': today_revenue,
        'today_transactions': today_transactions,
        'monthly_revenue': monthly_revenue,
        'monthly_transactions': monthly_transactions,
        'low_stock_count': low_stock_count,
        'out_of_stock': out_of_stock,
        'recent_sales': recent_sales,
        'pending_online_orders': pending_online_orders,
        'chart_data': chart_data,
        'top_products': top_products,
        'total_products': Product.objects.filter(is_active=True).count(),
    }
    return render(request, 'core/dashboard.html', context)
