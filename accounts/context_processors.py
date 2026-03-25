from .models import StaffProfile


def user_module_access(request):
    if not request.user.is_authenticated:
        return {}

    is_admin = request.user.is_superuser
    can_write = request.user.is_superuser
    can_view_financials = request.user.is_superuser
    can_view_store = request.user.is_superuser
    modules = {key: True for key, _ in StaffProfile.MODULES}

    try:
        profile = request.user.staff_profile
        is_admin = is_admin or profile.is_admin_level
        can_write = can_write or profile.can_write
        can_view_financials = can_view_financials or profile.can_view_financials
        can_view_store = can_view_store or profile.can_view_store
        modules = {key: profile.has_module_access(key) for key, _ in StaffProfile.MODULES}
    except Exception:
        pass

    return {
        'user_modules': modules,
        'user_is_admin': is_admin,
        'user_can_write': can_write,
        'user_can_view_financials': can_view_financials,
        'user_can_view_store': can_view_store,
    }
