# backend/django_app/jobs/urls.py

from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import JobListingViewSet

# Create router once per import.
router = SimpleRouter()
router.register(r'', JobListingViewSet, basename='job')

urlpatterns = router.urls

