# backend/django_app/applications/urls.py
from django.urls import path
from rest_framework.routers import SimpleRouter
from .views import ApplicationQueueViewSet, ApplicationViewSet, CoverLetterViewSet

router = SimpleRouter()
router.register(r'queue', ApplicationQueueViewSet, basename='queue')
router.register(r'applications', ApplicationViewSet, basename='application')
router.register(r'cover-letters', CoverLetterViewSet, basename='cover-letter')

urlpatterns = router.urls
