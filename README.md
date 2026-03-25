# Guide Bookshop & Stationeries — ERP System

A full-featured Django ERP application for bookshop management with an integrated ecommerce storefront.

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install django pillow

# 2. Run migrations
python manage.py migrate

# 3. Load sample data
python seed_data.py

# 4. Start the server
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` for the public store.

---

## 🔐 Login Credentials

| Role     | Username   | Password     | Access         |
|----------|------------|--------------|----------------|
| Admin    | admin      | admin123     | Full access    |
| Manager  | manager1   | manager123   | Reports + Mgmt |
| Cashier  | cashier1   | cashier123   | POS + Sales    |

Staff Portal: `http://127.0.0.1:8000/accounts/login/`

---

## 📦 Module Overview

### Public / Ecommerce (`/shop/`)
- **Homepage** — Hero banner, featured products, new arrivals, categories
- **Shop** — Full product catalogue with search, filter, sort
- **Product Detail** — Images, descriptions, add to cart
- **Shopping Cart** — Update quantities, remove items
- **Checkout** — Guest checkout, payment method selection
- **Order Tracking** — View order status by order number

### Staff Portal (`/dashboard/`)

#### 🖥️ Point of Sale (`/sales/pos/`)
- Real-time product search by name or SKU
- Category filter for quick navigation
- Cart with quantity management
- Discount field
- Cash change calculator
- Instant receipt generation
- AJAX-powered (no page reload)

#### 📊 Sales Management (`/sales/`)
- Sale history with date/status/customer filters
- Manual sale entry form
- Customer management
- Invoice printing
- Expense tracking

#### 📦 Inventory (`/inventory/`)
- Product CRUD with image upload
- SKU auto-generation
- Cost price, selling price, discount price
- Stock level tracking with alerts
- Stock movement history (in/out/adjustment/damage)
- Low stock report
- Purchase Orders from suppliers
- Receive stock against POs

#### 🌐 Online Orders (`/shop/orders/manage/`)
- View all ecommerce orders
- Update order status (Pending → Confirmed → Shipped → Delivered)
- Filter by status

#### 📈 Reports (`/sales/reports/`)
- Revenue, profit, expenses overview
- Date period selector (Today/Week/Month/Year)
- Revenue trend chart
- Payment method breakdown (doughnut chart)
- Top selling products

#### 👥 Staff Management (`/accounts/staff/`)
- Add/edit staff with roles
- Roles: Admin, Manager, Cashier, Inventory Clerk, Sales Associate
- Auto-generated employee IDs

---

## 🛠️ Technology Stack

| Layer     | Technology                    |
|-----------|-------------------------------|
| Backend   | Django 4.x (MVT)              |
| Frontend  | Django Templates + Tailwind CSS CDN |
| Charts    | Chart.js 4.x                  |
| Icons     | Font Awesome 6                |
| Fonts     | Google Fonts (Playfair Display + Inter) |
| Database  | SQLite (dev) / PostgreSQL (prod) |
| Images    | Pillow                        |

---

## 📁 Project Structure

```
guide_bookshop/
├── guide_bookshop/     # Main config (settings, urls)
├── core/               # Landing page, dashboard, context processors
├── accounts/           # Staff auth, profiles
├── inventory/          # Products, categories, suppliers, POs, stock
├── sales/              # POS, sales, customers, expenses, reports
├── ecommerce/          # Online shop, cart, online orders
├── templates/          # All HTML templates
│   ├── base_public.html    # Public site layout (header, footer)
│   ├── base_admin.html     # Staff portal layout (sidebar)
│   ├── core/
│   ├── accounts/
│   ├── inventory/
│   ├── sales/
│   └── ecommerce/
├── static/             # CSS, JS, images
├── media/              # User uploads (product images)
├── seed_data.py        # Demo data loader
└── manage.py
```

---

## ⚙️ Production Deployment Notes

1. Change `SECRET_KEY` in settings.py
2. Set `DEBUG = False`
3. Configure `ALLOWED_HOSTS`
4. Use PostgreSQL instead of SQLite
5. Set up a proper `MEDIA_ROOT` with cloud storage (e.g., AWS S3)
6. Run `collectstatic` for production static files
7. Use Gunicorn + Nginx in production

---

## 🎨 Theme

- **Primary Color**: Green (`#16a34a` - Tailwind primary-600)
- **Typography**: Playfair Display (headings) + Inter (body)
- **Design**: Clean cards, rounded corners, minimal shadows
