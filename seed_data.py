import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guide_bookshop.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import StaffProfile
from inventory.models import Category, Product, Supplier
from core.models import SiteSettings, Announcement
from django.utils.text import slugify
import uuid

# Site settings
SiteSettings.objects.get_or_create(defaults={
    'shop_name': 'Guide Bookshop & Stationeries',
    'tagline': 'Your Knowledge Partner',
    'address': '12 Lagos-Ibadan Expressway, Ojota, Lagos, Nigeria',
    'phone': '0800-GUIDE-BS (08003443227)',
    'email': 'info@guidebookshop.ng',
    'about_us': 'Guide Bookshop & Stationeries has been serving Nigerians with quality books and stationeries since our founding.',
    'whatsapp_number': '2348012345678',
})

Announcement.objects.get_or_create(message="Free delivery on orders above ₦10,000! 📚 New academic books just arrived.")

# Superuser
if not User.objects.filter(username='admin').exists():
    admin_user = User.objects.create_superuser('admin', 'admin@guidebookshop.ng', 'admin123')
    admin_user.first_name = 'Super'
    admin_user.last_name = 'Admin'
    admin_user.save()
    StaffProfile.objects.create(user=admin_user, role='admin', employee_id='EMP-ADMIN-001', phone='08012345678')
    print("Superuser 'admin' created (password: admin123)")

# Staff
if not User.objects.filter(username='cashier1').exists():
    cashier = User.objects.create_user('cashier1', 'cashier@guidebookshop.ng', 'cashier123')
    cashier.first_name = 'Amaka'
    cashier.last_name = 'Obi'
    cashier.save()
    StaffProfile.objects.create(user=cashier, role='cashier', employee_id='EMP-CSH-001', phone='08098765432')
    print("Cashier 'cashier1' created (password: cashier123)")

if not User.objects.filter(username='manager1').exists():
    manager = User.objects.create_user('manager1', 'manager@guidebookshop.ng', 'manager123')
    manager.first_name = 'Emeka'
    manager.last_name = 'Nwosu'
    manager.save()
    StaffProfile.objects.create(user=manager, role='manager', employee_id='EMP-MGR-001', phone='07087654321')
    print("Manager 'manager1' created (password: manager123)")

# Suppliers
supplier1, _ = Supplier.objects.get_or_create(name='Longman Nigeria Ltd', defaults={
    'contact_person': 'Mr. Adeyemi', 'phone': '0801-234-5678', 'email': 'sales@longman.com.ng'
})
supplier2, _ = Supplier.objects.get_or_create(name='Macmillan Publishers', defaults={
    'contact_person': 'Mrs. Bello', 'phone': '0802-345-6789', 'email': 'orders@macmillan.com.ng'
})

# Categories
categories_data = [
    ('Fiction', 'fiction', 'Novels, short stories, and fictional works'),
    ('Non-Fiction', 'non-fiction', 'Factual books, biographies, and more'),
    ('Academic', 'academic', 'Textbooks and academic materials'),
    ('Children Books', 'children-books', 'Books for young readers'),
    ('Stationery', 'stationery', 'Pens, pencils, notebooks and office supplies'),
    ('Art Supplies', 'art-supplies', 'Drawing and painting materials'),
    ('Educational Tools', 'educational-tools', 'Learning aids and educational materials'),
    ('Professional Books', 'professional-books', 'Business, law, medical and professional books'),
]
cats = {}
for name, slug, desc in categories_data:
    cat, _ = Category.objects.get_or_create(slug=slug, defaults={'name': name, 'description': desc})
    cats[slug] = cat

# Products
products_data = [
    ('Things Fall Apart', 'Chinua Achebe', 'Fiction', 'fiction', 'A masterpiece of world literature.', 1200, 1800, 500, True),
    ('Purple Hibiscus', 'Chimamanda Ngozi Adichie', 'Fiction', 'fiction', 'A powerful debut novel.', 1500, 2200, 350, True),
    ('Half of a Yellow Sun', 'Chimamanda Ngozi Adichie', 'Fiction', 'fiction', 'Biafra war story.', 1800, 2500, 200, True),
    ('Senior Secondary Mathematics', 'MAN', 'Academic', 'academic', 'Complete SS1-SS3 textbook.', 2500, 3500, 150, True),
    ('Further Mathematics for Schools', 'T. Wiseman', 'Academic', 'academic', 'Advanced secondary maths.', 3000, 4200, 120, False),
    ('New General Mathematics SS1', 'MAN', 'Academic', 'academic', 'General maths textbook.', 2200, 3000, 200, True),
    ('English Grammar & Composition', 'P.O. Olatunde', 'Academic', 'academic', 'Comprehensive English guide.', 1800, 2500, 180, False),
    ('Integrated Science for JSS', 'Godwin Ojokojo', 'Academic', 'academic', 'Junior secondary science.', 1500, 2000, 300, False),
    ('The Bluest Eye', 'Toni Morrison', 'Fiction', 'fiction', 'Nobel laureate classic.', 2000, 3000, 100, True),
    ('Business Administration Today', 'Various Authors', 'Professional Books', 'professional-books', 'Business management guide.', 3500, 5000, 80, False),
    ('Ballpoint Pens (Pack of 10)', '', 'Stationery', 'stationery', 'Smooth writing ballpoint pens, blue.', 500, 800, 500, False),
    ('A4 Ruled Exercise Books (10 pcs)', '', 'Stationery', 'stationery', 'Quality lined exercise books.', 800, 1200, 300, False),
    ('Mathematical Set (Compass)', '', 'Stationery', 'stationery', 'Complete geometric instruments set.', 600, 900, 250, False),
    ('Watercolor Paint Set 24 Colors', '', 'Art Supplies', 'art-supplies', 'Professional watercolor paints.', 1500, 2200, 100, True),
    ('Sketch Pad A3', '', 'Art Supplies', 'art-supplies', 'Premium quality sketch paper.', 700, 1100, 150, False),
    ('Abacus for Kids', '', 'Educational Tools', 'educational-tools', 'Counting aid for early learners.', 800, 1200, 200, False),
    ('My First Dictionary', 'Various', 'Children Books', 'children-books', 'Illustrated picture dictionary.', 1200, 1800, 120, True),
    ('The Lion and the Jewel', 'Wole Soyinka', 'Fiction', 'fiction', 'Nobel laureate drama.', 1000, 1500, 150, True),
    ('Notebook (Hardcover, A5)', '', 'Stationery', 'stationery', 'Premium hardcover notebook.', 600, 950, 400, False),
    ('WAEC Past Questions Bundle', 'WAEC', 'Academic', 'academic', '10 years past questions, all subjects.', 2000, 3000, 200, True),
]

for name, author, cat_name, cat_slug, desc, cost, price, qty, featured in products_data:
    slug_base = slugify(name)
    slug = slug_base
    if Product.objects.filter(slug=slug).exists():
        continue
    
    product_type = 'book'
    if cat_slug == 'stationery':
        product_type = 'stationery'
    elif cat_slug == 'art-supplies':
        product_type = 'art_supply'
    elif cat_slug == 'educational-tools':
        product_type = 'educational'
    
    Product.objects.create(
        name=name,
        slug=slug,
        sku=f"SKU-{str(uuid.uuid4())[:8].upper()}",
        product_type=product_type,
        category=cats.get(cat_slug),
        supplier=supplier1,
        description=desc,
        author=author,
        cost_price=cost,
        selling_price=price,
        quantity_in_stock=qty,
        reorder_level=10,
        is_featured=featured,
        is_active=True,
        is_available_online=True,
    )

print(f"\n✅ Seed data loaded successfully!")
print(f"Products: {Product.objects.count()}")
print(f"Categories: {Category.objects.count()}")
print(f"\n--- LOGIN CREDENTIALS ---")
print("Admin:   admin / admin123")
print("Cashier: cashier1 / cashier123")
print("Manager: manager1 / manager123")
