from django.contrib import messages
from django.core.cache import cache
from django.shortcuts import redirect

_LOGIN_PATH = '/accounts/login/'
_MAX_ATTEMPTS = 5
_LOCKOUT_SECONDS = 600  # 10 minutes


def _client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    return forwarded.split(',')[0].strip() if forwarded else request.META.get('REMOTE_ADDR', '')


class LoginRateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == _LOGIN_PATH and request.method == 'POST':
            ip = _client_ip(request)
            username = request.POST.get('username', '')[:64]
            ip_key = f'login_attempts_ip_{ip}'
            user_key = f'login_attempts_user_{username}' if username else None

            ip_attempts = cache.get(ip_key, 0)
            user_attempts = cache.get(user_key, 0) if user_key else 0

            if ip_attempts >= _MAX_ATTEMPTS or user_attempts >= _MAX_ATTEMPTS:
                messages.error(
                    request,
                    'Too many failed login attempts. Please try again in 10 minutes.',
                )
                return redirect(_LOGIN_PATH)

            response = self.get_response(request)

            if response.status_code == 200:
                # Failed login — increment both counters
                cache.set(ip_key, ip_attempts + 1, _LOCKOUT_SECONDS)
                if user_key:
                    cache.set(user_key, user_attempts + 1, _LOCKOUT_SECONDS)
            else:
                # Successful login — clear counters
                cache.delete(ip_key)
                if user_key:
                    cache.delete(user_key)
            return response
        return self.get_response(request)
