from ecommerce.models import Cart, CartItem
from .models import SiteSettings, Announcement


def cart_context(request):
    cart_count = 0
    if request.session.session_key:
        try:
            cart = Cart.objects.get(session_key=request.session.session_key)
            cart_count = cart.items.count()
        except Cart.DoesNotExist:
            pass
    return {'cart_count': cart_count}


def site_context(request):
    try:
        settings = SiteSettings.objects.first()
    except:
        settings = None
    
    announcements = Announcement.objects.filter(is_active=True)
    return {
        'site_settings': settings,
        'announcements': announcements,
    }
