from django.contrib import admin
from .models import SiteSettings, Banner, Announcement
admin.site.register(SiteSettings)
admin.site.register(Banner)
admin.site.register(Announcement)
