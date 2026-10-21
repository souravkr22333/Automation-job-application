# backend/django_app/core/middleware.py (add AuditMiddleware)
import logging
import time
import uuid
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.core.cache import cache
from .models import AuditLog

logger = logging.getLogger(__name__)


class AuditMiddleware(MiddlewareMixin):
    """Log API calls for audit purposes"""
    
    def process_request(self, request):
        request.start_time = time.time()
        request.request_id = str(uuid.uuid4())
        request.META['X-Request-ID'] = request.request_id
    
    def process_response(self, request, response):
        # Skip logging for certain paths
        skip_paths = ['/admin/', '/static/', '/media/', '/health']
        if any(request.path.startswith(path) for path in skip_paths):
            return response
        
        # Log API calls
        if request.path.startswith('/api/'):
            try:
                user_id = request.user.id if request.user.is_authenticated else None
                AuditLog.objects.create(
                    user_id=user_id,
                    action=AuditLog.Action.API_CALL,
                    resource_type='api',
                    ip_address=self._get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    request_path=request.path,
                    request_method=request.method,
                    changes={
                        'status': response.status_code,
                        'duration': time.time() - request.start_time
                    }
                )
            except Exception as e:
                logger.error(f"Audit log error: {str(e)}")
        
        return response
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')