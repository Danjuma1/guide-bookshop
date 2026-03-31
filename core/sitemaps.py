from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.conf import settings
from inventory.models import Product, Category


class SEOSitemapMixin:
    protocol = 'https'

    def get_domain(self, site=None):
        return 'guidebookshop.com.ng'


class StaticViewSitemap(SEOSitemapMixin, Sitemap):
    priority = 1.0
    changefreq = 'weekly'

    def items(self):
        return ['landing', 'shop_home', 'about', 'contact']

    def location(self, item):
        return reverse(item)


class ProductSitemap(SEOSitemapMixin, Sitemap):
    changefreq = 'weekly'
    priority = 0.9

    def items(self):
        return Product.objects.filter(is_active=True, is_available_online=True)

    def location(self, obj):
        return reverse('shop_product_detail', args=[obj.slug])

    def lastmod(self, obj):
        return obj.updated_at


class CategorySitemap(SEOSitemapMixin, Sitemap):
    changefreq = 'monthly'
    priority = 0.7

    def items(self):
        return Category.objects.all()

    def location(self, obj):
        return reverse('category_products', args=[obj.slug])
