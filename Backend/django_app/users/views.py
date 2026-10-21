# backend/django_app/users/views.py
from rest_framework import status, generics, permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.core.cache import cache
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.conf import settings
import jwt
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import jwt
from datetime import datetime, timedelta





from .models import (
    User, Education, Experience, Project, Certification, Language
)
from .serializers import (
    UserProfileSerializer, UserProfileUpdateSerializer,
    UserPreferencesSerializer, UserRegisterSerializer,
    CustomTokenObtainPairSerializer,
    EducationSerializer, EducationCreateUpdateSerializer,
    ExperienceSerializer, ExperienceCreateUpdateSerializer,
    ProjectSerializer, ProjectCreateUpdateSerializer,
    CertificationSerializer, CertificationCreateUpdateSerializer,
    LanguageSerializer
)


# ============================================================
# Authentication Views
# ============================================================
class RegisterView(APIView):
    """User registration endpoint"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserProfileSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(TokenObtainPairView):
    """JWT Login endpoint"""
    permission_classes = [permissions.AllowAny]
    serializer_class = CustomTokenObtainPairSerializer


# ============================================================
# User Profile Views
# ============================================================
class UserProfileView(generics.RetrieveUpdateAPIView):
    """User profile management"""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = UserProfileUpdateSerializer(
            instance, 
            data=request.data, 
            partial=partial
        )
        
        if serializer.is_valid():
            self.perform_update(serializer)
            
            # Clear cache
            cache.delete(f'user_{instance.id}_profile')
            
            return Response({
                'status': 'success',
                'message': 'Profile updated successfully',
                'data': UserProfileSerializer(instance).data
            })
        
        return Response({
            'status': 'error',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class UserPreferencesView(APIView):
    """User preferences management"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        return Response({
            'status': 'success',
            'data': request.user.preferences
        })
    
    def put(self, request):
        serializer = UserPreferencesSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            user.preferences = serializer.validated_data
            user.save()
            
            # Clear cache
            cache.delete(f'user_{user.id}_preferences')
            
            return Response({
                'status': 'success',
                'data': user.preferences
            })
        
        return Response({
            'status': 'error',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class UserSkillsView(APIView):
    """User skills management"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        return Response({
            'status': 'success',
            'data': {
                'skills': request.user.skills,
                'count': len(request.user.skills)
            }
        })
    
    def post(self, request):
        """Add multiple skills"""
        skills = request.data.get('skills', [])
        
        if not skills:
            return Response({
                'status': 'error',
                'message': 'Skills list is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Merge and deduplicate
        current_skills = set(request.user.skills)
        new_skills = set(skills)
        request.user.skills = list(current_skills | new_skills)
        request.user.save()
        
        # Clear cache
        cache.delete(f'user_{request.user.id}_skills')
        
        return Response({
            'status': 'success',
            'message': f'Added {len(new_skills)} skills',
            'data': {
                'skills': request.user.skills,
                'added': list(new_skills),
                'count': len(request.user.skills)
            }
        })
    
    def delete(self, request):
        """Remove multiple skills"""
        skills_to_remove = request.data.get('skills', [])
        
        if not skills_to_remove:
            return Response({
                'status': 'error',
                'message': 'Skills list is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        current_skills = set(request.user.skills)
        to_remove = set(skills_to_remove)
        request.user.skills = list(current_skills - to_remove)
        request.user.save()
        
        # Clear cache
        cache.delete(f'user_{request.user.id}_skills')
        
        return Response({
            'status': 'success',
            'message': f'Removed {len(to_remove)} skills',
            'data': {
                'skills': request.user.skills,
                'removed': list(to_remove),
                'count': len(request.user.skills)
            }
        })


class UserPreferredJobsView(APIView):
    """User preferred jobs management"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        return Response({
            'status': 'success',
            'data': {
                'preferred_job_titles': request.user.preferred_job_titles,
                'count': len(request.user.preferred_job_titles)
            }
        })
    
    def post(self, request):
        jobs = request.data.get('jobs', [])
        
        if not jobs:
            return Response({
                'status': 'error',
                'message': 'Jobs list is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        current_jobs = set(request.user.preferred_job_titles)
        new_jobs = set(jobs)
        request.user.preferred_job_titles = list(current_jobs | new_jobs)
        request.user.save()
        
        return Response({
            'status': 'success',
            'data': {
                'preferred_job_titles': request.user.preferred_job_titles,
                'count': len(request.user.preferred_job_titles)
            }
        })


class UserPreferredLocationsView(APIView):
    """User preferred locations management"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        return Response({
            'status': 'success',
            'data': {
                'preferred_locations': request.user.preferred_locations,
                'count': len(request.user.preferred_locations)
            }
        })
    
    def post(self, request):
        locations = request.data.get('locations', [])
        
        if not locations:
            return Response({
                'status': 'error',
                'message': 'Locations list is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        current_locations = set(request.user.preferred_locations)
        new_locations = set(locations)
        request.user.preferred_locations = list(current_locations | new_locations)
        request.user.save()
        
        return Response({
            'status': 'success',
            'data': {
                'preferred_locations': request.user.preferred_locations,
                'count': len(request.user.preferred_locations)
            }
        })


# ============================================================
# Education Views
# ============================================================
class EducationViewSet(viewsets.ModelViewSet):
    """Education management endpoints"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EducationSerializer
    
    def get_queryset(self):
        return Education.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return EducationCreateUpdateSerializer
        return EducationSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        cache.delete(f'user_{self.request.user.id}_educations')
    
    def perform_update(self, serializer):
        serializer.save()
        cache.delete(f'user_{self.request.user.id}_educations')
    
    def perform_destroy(self, instance):
        instance.delete()
        cache.delete(f'user_{self.request.user.id}_educations')


# ============================================================
# Experience Views
# ============================================================
class ExperienceViewSet(viewsets.ModelViewSet):
    """Experience management endpoints"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ExperienceSerializer
    
    def get_queryset(self):
        return Experience.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ExperienceCreateUpdateSerializer
        return ExperienceSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        cache.delete(f'user_{self.request.user.id}_experiences')
    
    def perform_update(self, serializer):
        serializer.save()
        cache.delete(f'user_{self.request.user.id}_experiences')
    
    def perform_destroy(self, instance):
        instance.delete()
        cache.delete(f'user_{self.request.user.id}_experiences')


# ============================================================
# Project Views
# ============================================================
class ProjectViewSet(viewsets.ModelViewSet):
    """Project management endpoints"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProjectSerializer
    
    def get_queryset(self):
        return Project.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ProjectCreateUpdateSerializer
        return ProjectSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        cache.delete(f'user_{self.request.user.id}_projects')
    
    def perform_update(self, serializer):
        serializer.save()
        cache.delete(f'user_{self.request.user.id}_projects')
    
    def perform_destroy(self, instance):
        instance.delete()
        cache.delete(f'user_{self.request.user.id}_projects')


# ============================================================
# Certification Views
# ============================================================
class CertificationViewSet(viewsets.ModelViewSet):
    """Certification management endpoints"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CertificationSerializer
    
    def get_queryset(self):
        return Certification.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CertificationCreateUpdateSerializer
        return CertificationSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        cache.delete(f'user_{self.request.user.id}_certifications')
    
    def perform_update(self, serializer):
        serializer.save()
        cache.delete(f'user_{self.request.user.id}_certifications')
    
    def perform_destroy(self, instance):
        instance.delete()
        cache.delete(f'user_{self.request.user.id}_certifications')


# ============================================================
# Language Views
# ============================================================
class LanguageViewSet(viewsets.ModelViewSet):
    """Language management endpoints"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LanguageSerializer
    
    def get_queryset(self):
        return Language.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        cache.delete(f'user_{self.request.user.id}_languages')
    
    def perform_update(self, serializer):
        serializer.save()
        cache.delete(f'user_{self.request.user.id}_languages')
    
    def perform_destroy(self, instance):
        instance.delete()
        cache.delete(f'user_{self.request.user.id}_languages')


# ============================================================
# Complete Profile View
# ============================================================
class CompleteProfileView(APIView):
    """Get complete user profile with all sections"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        cache_key = f'user_{user.id}_complete_profile'
        
        # Try cache
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response({
                'status': 'success',
                'data': cached_data,
                'cached': True
            })
        
        # Get all data
        serializer = UserProfileSerializer(user)
        data = serializer.data
        
        # Cache for 5 minutes
        cache.set(cache_key, data, 300)
        
        return Response({
            'status': 'success',
            'data': data
        })





# # backend/django_app/users/views.py
# from rest_framework import status, generics, permissions
# from rest_framework.response import Response
# from rest_framework.views import APIView
# from rest_framework_simplejwt.tokens import RefreshToken
# from rest_framework_simplejwt.views import TokenObtainPairView
# from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
# from django.core.cache import cache
# from .models import User
# from django.core.mail import send_mail
# from django.template.loader import render_to_string
# from django.utils.html import strip_tags
# from django.conf import settings
# import jwt
# import uuid
# from datetime import datetime, timedelta
# from .models import User
# from .serializers import (
#     UserSerializer, 
#     UserProfileSerializer, 
#     UserPreferencesSerializer,
#     CustomTokenObtainPairSerializer
# )

# class RegisterView(APIView):
#     """User registration endpoint"""
#     permission_classes = [permissions.AllowAny]
    
#     def post(self, request):
#         serializer = UserSerializer(data=request.data)
#         if serializer.is_valid():
#             user = serializer.save()
#             refresh = RefreshToken.for_user(user)
            
#             return Response({
#                 'refresh': str(refresh),
#                 'access': str(refresh.access_token),
#                 'user': UserSerializer(user).data
#             }, status=status.HTTP_201_CREATED)
        
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class LoginView(TokenObtainPairView):
#     """JWT Login endpoint"""
#     permission_classes = [permissions.AllowAny]
#     serializer_class = CustomTokenObtainPairSerializer


# class UserProfileView(generics.RetrieveUpdateAPIView):
#     """User profile management"""
#     serializer_class = UserProfileSerializer
#     permission_classes = [permissions.IsAuthenticated]
    
#     def get_object(self):
#         return self.request.user


# class UserPreferencesView(APIView):
#     """User preferences management"""
#     permission_classes = [permissions.IsAuthenticated]
    
#     def get(self, request):
#         return Response(request.user.preferences)
    
#     def put(self, request):
#         serializer = UserPreferencesSerializer(data=request.data)
#         if serializer.is_valid():
#             user = request.user
#             user.preferences = serializer.validated_data
#             user.save()
            
#             # Clear cache
#             cache.delete(f'user_preferences_{user.id}')
            
#             return Response(user.preferences)
        
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """Logout endpoint - blacklist refresh token"""
    # Logout should still work even if the access token is expired.
    # We blacklist based on the refresh token.
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token is required'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            token = RefreshToken(refresh_token)

            # SimpleJWT blacklist provides `token.blacklist()` only when the
            # blacklist app is installed and properly configured.
            # Avoid failing logout when blacklist isn't available.
            if hasattr(token, 'blacklist'):
                token.blacklist()

            return Response({'message': 'Successfully logged out'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


        


class VerifyEmailView(APIView):
    """Email verification endpoint"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, token):
        try:
            # Decode token
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('user_id')
            
            if not user_id:
                return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
            
            user = User.objects.get(id=user_id)
            user.is_active = True
            user.save()
            
            return Response({'message': 'Email verified successfully'})
        except jwt.ExpiredSignatureError:
            return Response({'error': 'Token expired'}, status=status.HTTP_400_BAD_REQUEST)
        except jwt.InvalidTokenError:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


class ResendVerificationView(APIView):
    """Resend verification email"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
            
            if user.is_active:
                return Response({'message': 'Email already verified'})
            
            # Generate verification token
            token = jwt.encode(
                {
                    'user_id': str(user.id),
                    'exp': datetime.utcnow() + timedelta(hours=24)
                },
                settings.SECRET_KEY,
                algorithm='HS256'
            )
            
            # Send email
            verification_link = f"{settings.FRONTEND_URL}/verify-email/{token}"
            html_message = render_to_string('email/verification.html', {
                'user': user,
                'verification_link': verification_link
            })
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject='Verify Your Email',
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message
            )
            
            return Response({'message': 'Verification email sent'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        



# backend/django_app/users/views.py (add password reset)

class PasswordResetRequestView(APIView):
    """Request password reset"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
            
            # Generate reset token
            token = jwt.encode(
                {
                    'user_id': str(user.id),
                    'type': 'password_reset',
                    'exp': datetime.utcnow() + timedelta(hours=1)
                },
                settings.SECRET_KEY,
                algorithm='HS256'
            )
            
            # Send reset email
            reset_link = f"{settings.FRONTEND_URL}/reset-password/{token}"
            html_message = render_to_string('email/password_reset.html', {
                'user': user,
                'reset_link': reset_link
            })
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject='Password Reset Request',
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message
            )
            
            return Response({'message': 'Password reset email sent'})
        except User.DoesNotExist:
            # Don't reveal if user exists or not
            return Response({'message': 'If an account exists, a reset email has been sent'})


class PasswordResetConfirmView(APIView):
    """Confirm password reset"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, token):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            
            if payload.get('type') != 'password_reset':
                return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
            
            user_id = payload.get('user_id')
            new_password = request.data.get('new_password')
            confirm_password = request.data.get('confirm_password')
            
            if not new_password or not confirm_password:
                return Response({'error': 'Password is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            if new_password != confirm_password:
                return Response({'error': 'Passwords do not match'}, status=status.HTTP_400_BAD_REQUEST)
            
            user = User.objects.get(id=user_id)
            user.set_password(new_password)
            user.save()
            
            return Response({'message': 'Password reset successfully'})
        except jwt.ExpiredSignatureError:
            return Response({'error': 'Token expired'}, status=status.HTTP_400_BAD_REQUEST)
        except jwt.InvalidTokenError:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)