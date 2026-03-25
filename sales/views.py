from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from datetime import date, timedelta
import json, csv, io
from decimal import Decimal
from .models import Sale, SaleItem, Customer, Expense, DailySummary
from inventory.models import Product, StockMovement
from accounts.decorators import module_required, write_required


@login_required
@module_required('sales')
def sale_list(request):
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    status = request.GET.get('status', '')
    payment = request.GET.get('payment', '')
    q = request.GET.get('q', '')
    sort = request.GET.get('sort', '-sale_date')

    db_sorts = {
        'sale_date', '-sale_date',
        'invoice_number', '-invoice_number',
        'customer__name', '-customer__name',
    }
    if sort not in db_sorts and sort not in ('total_amount', '-total_amount'):
        sort = '-sale_date'

    db_sort = sort if sort in db_sorts else '-sale_date'
    sales = Sale.objects.select_related('customer', 'served_by').order_by(db_sort)

    if date_from:
        sales = sales.filter(sale_date__date__gte=date_from)
    if date_to:
        sales = sales.filter(sale_date__date__lte=date_to)
    if status:
        sales = sales.filter(status=status)
    if payment:
        sales = sales.filter(payment_method=payment)
    if q:
        sales = sales.filter(Q(invoice_number__icontains=q) | Q(customer__name__icontains=q))

    sales = list(sales)
    if sort == 'total_amount':
        sales.sort(key=lambda s: s.total_amount)
    elif sort == '-total_amount':
        sales.sort(key=lambda s: s.total_amount, reverse=True)

    total_revenue = sum(s.total_amount for s in sales if s.status == 'completed')
    return render(request, 'sales/sale_list.html', {
        'sales': sales, 'total_revenue': total_revenue,
        'date_from': date_from, 'date_to': date_to,
        'status': status, 'payment': payment, 'q': q, 'sort': sort,
    })


@login_required
@module_required('pos')
def pos_view(request):
    from inventory.models import Category
    products = Product.objects.filter(is_active=True, quantity_in_stock__gt=0).select_related('category')
    categories = Category.objects.filter(
        products__is_active=True, products__quantity_in_stock__gt=0
    ).distinct().order_by('name')
    return render(request, 'sales/pos.html', {
        'products': products,
        'categories': categories,
    })


@login_required
@module_required('pos')
def new_sale(request):
    if request.method == 'POST':
        customer_id = request.POST.get('customer_id')
        payment_method = request.POST.get('payment_method', 'cash')
        discount = Decimal(str(request.POST.get('discount_amount', 0) or 0))
        notes = request.POST.get('notes', '')
        product_ids = request.POST.getlist('product_id')
        quantities = request.POST.getlist('quantity')
        prices = request.POST.getlist('unit_price')

        customer = None
        if customer_id:
            try:
                customer = Customer.objects.get(pk=customer_id)
            except Customer.DoesNotExist:
                pass

        sale = Sale.objects.create(
            customer=customer,
            served_by=request.user,
            payment_method=payment_method,
            discount_amount=discount,
            notes=notes,
            status='completed',
            payment_status=True,
        )

        for pid, qty, price in zip(product_ids, quantities, prices):
            if pid and qty:
                product = Product.objects.get(pk=pid)
                qty_int = int(qty)
                SaleItem.objects.create(
                    sale=sale, product=product,
                    quantity=qty_int,
                    unit_price=Decimal(str(price)),
                    unit_cost=product.cost_price,
                )
                prev = product.quantity_in_stock
                product.quantity_in_stock = max(0, product.quantity_in_stock - qty_int)
                product.save()
                StockMovement.objects.create(
                    product=product, movement_type='out',
                    quantity=qty_int, previous_stock=prev,
                    new_stock=product.quantity_in_stock,
                    reference=sale.invoice_number,
                    created_by=request.user,
                )

        messages.success(request, f'Sale {sale.invoice_number} recorded successfully.')
        return redirect('sale_detail', pk=sale.pk)

    customers = Customer.objects.all().order_by('name')
    products = Product.objects.filter(is_active=True, quantity_in_stock__gt=0)
    return render(request, 'sales/new_sale.html', {
        'customers': customers, 'products': products,
    })


@login_required
@module_required('sales')
def sale_detail(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    return render(request, 'sales/sale_detail.html', {'sale': sale})


@login_required
@module_required('sales')
def sale_invoice(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    return render(request, 'sales/invoice.html', {'sale': sale})


@login_required
@module_required('customers')
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    sales = customer.sales.order_by('-sale_date')
    total_spent = sum(s.total_amount for s in sales if s.status == 'completed')
    return render(request, 'sales/customer_detail.html', {
        'customer': customer, 'sales': sales, 'total_spent': total_spent,
    })


@login_required
@module_required('customers')
@write_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        customer.name = request.POST.get('name')
        customer.email = request.POST.get('email', '')
        customer.phone = request.POST.get('phone', '')
        customer.address = request.POST.get('address', '')
        customer.save()
        messages.success(request, 'Customer updated.')
        return redirect('customer_detail', pk=customer.pk)
    return render(request, 'sales/customer_form.html', {'customer': customer})


@login_required
@module_required('customers')
@write_required
def customer_delete(request, pk):
    if request.method == 'POST':
        customer = get_object_or_404(Customer, pk=pk)
        customer.delete()
        messages.success(request, 'Customer deleted.')
    return redirect('customer_list')


@login_required
@module_required('customers')
def customer_list(request):
    customers = Customer.objects.all().order_by('name')
    q = request.GET.get('q', '')
    if q:
        customers = customers.filter(Q(name__icontains=q) | Q(phone__icontains=q) | Q(email__icontains=q))
    return render(request, 'sales/customer_list.html', {'customers': customers, 'q': q})


@login_required
@module_required('customers')
@write_required
def customer_add(request):
    if request.method == 'POST':
        Customer.objects.create(
            name=request.POST.get('name'),
            email=request.POST.get('email', ''),
            phone=request.POST.get('phone', ''),
            address=request.POST.get('address', ''),
        )
        messages.success(request, 'Customer added.')
        return redirect('customer_list')
    return render(request, 'sales/customer_form.html')


@login_required
@module_required('expenses')
def expense_list(request):
    expenses = Expense.objects.order_by('-expense_date')
    month = request.GET.get('month', date.today().strftime('%Y-%m'))
    if month:
        year, m = month.split('-')
        expenses = expenses.filter(expense_date__year=year, expense_date__month=m)
    total = expenses.aggregate(t=Sum('amount'))['t'] or 0
    return render(request, 'sales/expense_list.html', {
        'expenses': expenses, 'total': total, 'month': month,
    })


@login_required
@module_required('expenses')
@write_required
def expense_edit(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        expense.title = request.POST.get('title')
        expense.category = request.POST.get('category')
        expense.amount = request.POST.get('amount')
        expense.description = request.POST.get('description', '')
        expense.expense_date = request.POST.get('expense_date') or date.today()
        expense.save()
        messages.success(request, 'Expense updated.')
        return redirect('expense_list')
    return render(request, 'sales/expense_form.html', {'expense': expense})


@login_required
@module_required('expenses')
@write_required
def expense_delete(request, pk):
    if request.method == 'POST':
        expense = get_object_or_404(Expense, pk=pk)
        expense.delete()
        messages.success(request, 'Expense deleted.')
    return redirect('expense_list')


@login_required
@module_required('expenses')
@write_required
def expense_add(request):
    if request.method == 'POST':
        Expense.objects.create(
            title=request.POST.get('title'),
            category=request.POST.get('category'),
            amount=request.POST.get('amount'),
            description=request.POST.get('description', ''),
            expense_date=request.POST.get('expense_date', date.today()),
            recorded_by=request.user,
        )
        messages.success(request, 'Expense recorded.')
        return redirect('expense_list')
    return render(request, 'sales/expense_form.html')


@login_required
@module_required('reports')
def reports_view(request):
    today = date.today()
    month_start = today.replace(day=1)
    period = request.GET.get('period', 'month')

    if period == 'today':
        start_date = today
    elif period == 'week':
        start_date = today - timedelta(days=7)
    elif period == 'month':
        start_date = month_start
    elif period == 'year':
        start_date = today.replace(month=1, day=1)
    else:
        start_date = month_start

    sales = Sale.objects.filter(sale_date__date__gte=start_date, status='completed')
    total_revenue = sum(s.total_amount for s in sales)
    total_profit = sum(s.total_profit for s in sales)
    total_transactions = sales.count()
    expenses = Expense.objects.filter(expense_date__gte=start_date)
    total_expenses = expenses.aggregate(t=Sum('amount'))['t'] or 0
    net_profit = total_profit - total_expenses

    # Sales by payment method
    payment_breakdown = {}
    for s in sales:
        pm = s.payment_method
        payment_breakdown[pm] = payment_breakdown.get(pm, 0) + float(s.total_amount)

    # Top selling products
    from sales.models import SaleItem
    from django.db.models import ExpressionWrapper, DecimalField, F as Fref
    top_products = SaleItem.objects.filter(
        sale__sale_date__date__gte=start_date,
        sale__status='completed'
    ).values('product__name').annotate(
        total_qty=Sum('quantity'),
        total_revenue=Sum(ExpressionWrapper(Fref('quantity') * Fref('unit_price'), output_field=DecimalField()))
    ).order_by('-total_qty')[:10]

    # Daily chart
    chart_data = []
    days = (today - start_date).days + 1
    for i in range(min(days, 30)):
        d = today - timedelta(days=(min(days, 30) - 1 - i))
        day_sales = Sale.objects.filter(sale_date__date=d, status='completed')
        day_rev = sum(s.total_amount for s in day_sales)
        chart_data.append({'date': d.strftime('%d %b'), 'revenue': float(day_rev)})

    context = {
        'total_revenue': total_revenue,
        'total_profit': total_profit,
        'total_transactions': total_transactions,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
        'payment_breakdown': payment_breakdown,
        'top_products': top_products,
        'chart_data': chart_data,
        'period': period,
        'start_date': start_date,
    }
    return render(request, 'sales/reports.html', context)


@login_required
@module_required('pos')
def product_search_api(request):
    q = request.GET.get('q', '')
    products = Product.objects.filter(
        Q(name__icontains=q) | Q(sku__icontains=q),
        is_active=True, quantity_in_stock__gt=0
    )[:10]
    data = [{
        'id': p.id,
        'name': p.name,
        'sku': p.sku,
        'price': float(p.effective_price),
        'stock': p.quantity_in_stock,
        'image': p.image.url if p.image else '',
    } for p in products]
    return JsonResponse({'products': data})


@login_required
@module_required('pos')
def process_sale_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            items = data.get('items', [])
            payment_method = data.get('payment_method', 'cash')
            discount = Decimal(str(data.get('discount', 0) or 0))
            customer_name = data.get('customer_name', '')

            customer = None
            if customer_name:
                customer, _ = Customer.objects.get_or_create(
                    name=customer_name,
                    defaults={'is_walk_in': True}
                )

            sale = Sale.objects.create(
                customer=customer,
                served_by=request.user,
                payment_method=payment_method,
                discount_amount=discount,
                status='completed',
                payment_status=True,
            )

            for item in items:
                product = Product.objects.get(pk=item['id'])
                qty = int(item['quantity'])
                SaleItem.objects.create(
                    sale=sale, product=product,
                    quantity=qty,
                    unit_price=Decimal(str(item['price'])),
                    unit_cost=product.cost_price,
                )
                prev = product.quantity_in_stock
                product.quantity_in_stock = max(0, product.quantity_in_stock - qty)
                product.save()
                StockMovement.objects.create(
                    product=product, movement_type='out',
                    quantity=qty, previous_stock=prev,
                    new_stock=product.quantity_in_stock,
                    reference=sale.invoice_number,
                    created_by=request.user,
                )

            return JsonResponse({
                'success': True,
                'invoice_number': sale.invoice_number,
                'total': float(sale.total_amount),
                'sale_id': sale.pk,
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'success': False}, status=405)


def _parse_upload(file):
    name = file.name.lower()
    if name.endswith('.csv'):
        decoded = file.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(decoded))
        return list(reader)
    elif name.endswith('.xlsx'):
        import openpyxl
        wb = openpyxl.load_workbook(filename=io.BytesIO(file.read()), read_only=True, data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return []
        headers = [str(h).strip() if h is not None else '' for h in rows[0]]
        result = []
        for row in rows[1:]:
            if all(v is None for v in row):
                continue
            result.append({headers[i]: (str(row[i]).strip() if row[i] is not None else '') for i in range(len(headers))})
        return result
    return []


@login_required
@module_required('imports')
def import_customers(request):
    HEADERS = ['Name', 'Email', 'Phone', 'Address']

    if request.GET.get('template') == 'xlsx':
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(HEADERS)
        for cell in ws[1]:
            cell.font = Font(bold=True, color='FFFFFF')
            cell.fill = PatternFill('solid', fgColor='166534')
            cell.alignment = Alignment(horizontal='center')
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = 22
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        resp = HttpResponse(buf.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        resp['Content-Disposition'] = 'attachment; filename="customers_template.xlsx"'
        return resp

    if request.GET.get('template') == 'csv':
        resp = HttpResponse(content_type='text/csv')
        resp['Content-Disposition'] = 'attachment; filename="customers_template.csv"'
        csv.writer(resp).writerow(HEADERS)
        return resp

    results = []
    if request.method == 'POST' and request.FILES.get('file'):
        rows = _parse_upload(request.FILES['file'])
        created = errors = 0
        for i, row in enumerate(rows, start=2):
            try:
                name = row.get('Name', '').strip()
                if not name:
                    continue
                Customer.objects.create(
                    name=name,
                    email=row.get('Email', ''),
                    phone=row.get('Phone', ''),
                    address=row.get('Address', ''),
                )
                results.append({'row': i, 'name': name, 'status': 'created'})
                created += 1
            except Exception as e:
                results.append({'row': i, 'name': row.get('Name', f'Row {i}'), 'status': 'error', 'error': str(e)})
                errors += 1
        messages.success(request, f'Import complete: {created} customer(s) added, {errors} error(s).')

    return render(request, 'sales/import_customers.html', {
        'entity': 'Customers', 'headers': HEADERS,
        'results': results,
    })


@login_required
@module_required('sales')
def sale_receipt(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    return render(request, 'sales/pos_receipt.html', {'sale': sale})
