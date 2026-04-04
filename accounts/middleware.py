from django.core.cache import cache
from django.http import HttpResponse

_LOGIN_PATH = '/accounts/login/'
_MAX_ATTEMPTS = 10
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
            key = f'login_attempts_{ip}'
            attempts = cache.get(key, 0)
            if attempts >= _MAX_ATTEMPTS:
                return HttpResponse(
                    'Too many login attempts. Please try again in 10 minutes.',
                    status=429,
                    content_type='text/plain',
                )
            response = self.get_response(request)
            # Increment counter on failed login (non-redirect response to POST)
            if response.status_code == 200:
                cache.set(key, attempts + 1, _LOCKOUT_SECONDS)
            else:
                cache.delete(key)
            return response
        return self.get_response(request)
