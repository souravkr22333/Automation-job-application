# backend/django_app/resumes/urls.py
from django.urls import path
from .views import ResumeViewSet

# Explicit routes (avoid DRF routers to prevent drf_format_suffix converter duplicate registration)
resume_list = ResumeViewSet.as_view({'get': 'list', 'post': 'upload'})
resume_detail = ResumeViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'update', 'delete': 'destroy'})
resume_current = ResumeViewSet.as_view({'get': 'current'})


urlpatterns = [
    # Resume endpoints
    path('', resume_list, name='resume-list'),
    path('current/', resume_current, name='resume-current'),
    path('<uuid:pk>/', resume_detail, name='resume-detail'),
    
  
]
