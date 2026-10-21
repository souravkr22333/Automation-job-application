# backend/django_app/users/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserProfileView, UserPreferencesView, UserSkillsView,
    UserPreferredJobsView, UserPreferredLocationsView,
    EducationViewSet, ExperienceViewSet, ProjectViewSet,
    CertificationViewSet, LanguageViewSet, CompleteProfileView,
    LogoutView , VerifyEmailView, ResendVerificationView , PasswordResetConfirmView, PasswordResetRequestView
)

router = DefaultRouter()
router.register(r'educations', EducationViewSet, basename='education')
router.register(r'experiences', ExperienceViewSet, basename='experience')
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'certifications', CertificationViewSet, basename='certification')
router.register(r'languages', LanguageViewSet, basename='language')

urlpatterns = [
    # Profile
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('profile/complete/', CompleteProfileView.as_view(), name='complete-profile'),
    
    # Preferences
    path('preferences/', UserPreferencesView.as_view(), name='user-preferences'),
    
    # Skills
    path('skills/', UserSkillsView.as_view(), name='user-skills'),
    
    # Preferred Jobs
    path('preferred-jobs/', UserPreferredJobsView.as_view(), name='user-preferred-jobs'),
    
    # Preferred Locations
    path('preferred-locations/', UserPreferredLocationsView.as_view(), name='user-preferred-locations'),
    
    # Logout
    path('logout/', LogoutView.as_view(), name='logout'),

    path('verify-email/<str:token>/', VerifyEmailView.as_view(), name='verify-email'),
    path('resend-verification/', ResendVerificationView.as_view(), name='resend-verification'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('password-reset/<str:token>/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    
    # Router URLs
    path('', include(router.urls)),
]




# # backend/django_app/users/urls.py
# from django.urls import path
# from .views import (
#     UserProfileView,
#     UserPreferencesView,
#     LogoutView,
#     VerifyEmailView,
#     ResendVerificationView,
#     PasswordResetRequestView,
#     PasswordResetConfirmView
# )

# urlpatterns = [
#     path('profile/', UserProfileView.as_view(), name='user-profile'),
#     path('preferences/', UserPreferencesView.as_view(), name='user-preferences'),
#     path('logout/', LogoutView.as_view(), name='logout'),
    # path('verify-email/<str:token>/', VerifyEmailView.as_view(), name='verify-email'),
    # path('resend-verification/', ResendVerificationView.as_view(), name='resend-verification'),
    # path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    # path('password-reset/<str:token>/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
# ]