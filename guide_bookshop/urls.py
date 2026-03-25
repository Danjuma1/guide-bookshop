from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('accounts/', include('accounts.urls')),
    path('inventory/', include('inventory.urls')),
    path('sales/', include('sales.urls')),
    path('shop/', include('ecommerce.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
