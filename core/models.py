from django.db import models


class SiteSettings(models.Model):
    shop_name = models.CharField(max_length=200, default="Guide Bookshop & Stationeries")
    tagline = models.CharField(max_length=300, blank=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    about_us = models.TextField(blank=True)
    logo = models.ImageField(upload_to='site/', blank=True, null=True)
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    google_maps_url = models.URLField(blank=True)
    whatsapp_number = models.CharField(max_length=20, blank=True)
    currency = models.CharField(max_length=5, default='₦')
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=7.5)

    class Meta:
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return self.shop_name


class Banner(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    image = models.ImageField(upload_to='banners/')
    link_url = models.CharField(max_length=200, blank=True)
    link_text = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class Announcement(models.Model):
    message = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message[:50]
