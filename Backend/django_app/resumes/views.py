# backend/django_app/resumes/views.py
import os
import uuid
import logging
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from django.db import transaction
from django.db.models import Q
from django.http import FileResponse, HttpResponse
from django.utils import timezone

from .models import Resume, ResumeVersion, TailoredResume
from .serializers import (
    ResumeSerializer, ResumeVersionSerializer, 
    ResumeUploadSerializer, ResumeTailorSerializer,
     ResumeDeleteSerializer,
    TailoredResumeSerializer, TailoredResumeEditSerializer
)
from .services import ResumeParser, ResumeStorageService, PDFGenerator
from .tasks import parse_resume_async, tailor_resume_async, extract_skills_with_openai

logger = logging.getLogger(__name__)


class ResumeViewSet(viewsets.ModelViewSet):
    """
    Resume management endpoints.
    Each user can have only ONE resume at a time.
    Uploading a new resume will replace the existing one.
    All files are stored in Supabase storage.
    """
    serializer_class = ResumeSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']
    
    def get_queryset(self):
        """Get resumes for the current user"""
        return Resume.objects.filter(user=self.request.user)
    
    def get_object(self):
        """Get a specific resume for the current user"""
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset, pk=self.kwargs['pk'])
        self.check_object_permissions(self.request, obj)
        return obj
    
    def get_user_resume(self):
        """Get the user's resume (singleton)"""
        return Resume.objects.filter(user=self.request.user).first()
    
    def get_cache_key(self, user_id: str, key: str = 'resume') -> str:
        """Generate cache key for user resume"""
        return f'resume_{user_id}_{key}'
    
    # ============================================================
    # 1. GET /api/resumes/ - Get current user's resume
    # ============================================================
    def list(self, request, *args, **kwargs):
        """
        Get the current user's resume.
        Since each user has only one resume, this returns a single object.
        """
        user_id = str(request.user.id)
        cache_key = self.get_cache_key(user_id, 'data')
        
        # Try cache first
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response({
                'status': 'success',
                'data': cached_data,
                'cached': True
            })
        
        resume = self.get_user_resume()
        
        if resume:
            serializer = self.get_serializer(resume)
            # Cache for 5 minutes
            cache.set(cache_key, serializer.data, 300)
            return Response({
                'status': 'success',
                'data': serializer.data
            })
        else:
            return Response({
                'status': 'success',
                'data': None,
                'message': 'No resume found. Please upload a resume.'
            }, status=status.HTTP_200_OK)
    
    # ============================================================
    # 2. GET /api/resumes/{id}/ - Get specific resume
    # ============================================================
    def retrieve(self, request, *args, **kwargs):
        """
        Get a specific resume by ID.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'status': 'success',
            'data': serializer.data
        })
    
    # ============================================================
    # 3. POST /api/resumes/ - Upload a new resume (replaces existing)
    # ============================================================
    @action(detail=False, methods=['POST'])
    def upload(self, request, *args, **kwargs):
        """
        Upload a new resume to Supabase storage.
        If a resume already exists for the user, it will be replaced.
        """
        upload_serializer = ResumeUploadSerializer(data=request.data)
        
        if not upload_serializer.is_valid():
            return Response({
                'status': 'error',
                'errors': upload_serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        file = upload_serializer.validated_data['file']
        name = upload_serializer.validated_data.get('name', file.name)
        is_default = upload_serializer.validated_data.get('is_default', True)
        
        storage_service = ResumeStorageService()
        
        try:
            with transaction.atomic():
                # Check if user already has a resume
                existing_resume = self.get_user_resume()
                
                if existing_resume:
                    # Delete existing resume from Supabase
                    storage_service.delete_resume(
                        str(request.user.id),
                        existing_resume.supabase_path
                    )
                    
                    # Delete versions
                    ResumeVersion.objects.filter(resume=existing_resume).delete()
                    existing_resume.delete()
                    logger.info(f"Replaced existing resume for user {request.user.id}")
                
                # Upload new resume to Supabase
                upload_result = storage_service.upload_resume(
                    str(request.user.id),
                    file
                )
                
                # Create resume record
                resume = Resume.objects.create(
                    user=request.user,
                    name=name,
                    supabase_url=upload_result['public_url'],
                    supabase_path=upload_result['path'],
                    supabase_bucket=upload_result['bucket'],
                    file_size=upload_result['file_size'],
                    file_type=upload_result['content_type'],
                    is_default=is_default,
                    version=1
                )
                
                # Trigger async parsing
                parse_resume_async.delay(str(resume.id))
                
                # Clear cache
                cache.delete(self.get_cache_key(str(request.user.id), 'data'))
                cache.delete(self.get_cache_key(str(request.user.id), 'check'))
                cache.delete(self.get_cache_key(str(request.user.id), 'stats'))
                
                serializer = self.get_serializer(resume)
                
                return Response({
                    'status': 'success',
                    'message': 'Resume uploaded successfully to Supabase. Processing in background.',
                    'data': serializer.data,
                    'supabase_url': upload_result['public_url']
                }, status=status.HTTP_201_CREATED)
                
        except ValueError as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception("Resume upload error")
            return Response({
                'status': 'error',
                'message': 'Failed to upload resume. Please check server logs.',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # ============================================================
    # 4. PUT /api/resumes/{id}/ - Update resume
    # ============================================================
    
    def update(self, request, *args, **kwargs):
        """
        Update an existing resume.
        """
        instance = self.get_object()
        
        # Only allow updating certain fields
        allowed_fields = ['name', 'is_default']
        update_data = {k: v for k, v in request.data.items() if k in allowed_fields}
        
        if not update_data:
            return Response({
                'status': 'error',
                'message': 'No valid fields to update'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(instance, data=update_data, partial=True)
        
        if serializer.is_valid():
            with transaction.atomic():
                # If setting as default, unset others
                if update_data.get('is_default', False):
                    Resume.objects.filter(
                        user=request.user,
                        is_default=True
                    ).exclude(id=instance.id).update(is_default=False)
                
                serializer.save()
                
                # Clear cache
                cache.delete(self.get_cache_key(str(request.user.id), 'data'))
                cache.delete(self.get_cache_key(str(request.user.id), 'check'))
                cache.delete(self.get_cache_key(str(request.user.id), 'stats'))
            
            return Response({
                'status': 'success',
                'message': 'Resume updated successfully',
                'data': serializer.data
            })
        
        return Response({
            'status': 'error',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # ============================================================
    # 5. DELETE /api/resumes/{id}/ - Delete resume
    # ============================================================
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete a resume from both database and Supabase storage.
        """
        instance = self.get_object()
        
        storage_service = ResumeStorageService()
        
        with transaction.atomic():
            # Delete from Supabase
            storage_service.delete_resume(
                str(request.user.id),
                instance.supabase_path
            )
            
            # Delete versions
            ResumeVersion.objects.filter(resume=instance).delete()
            instance.delete()
            
            # Clear cache
            cache.delete(self.get_cache_key(str(request.user.id), 'data'))
            cache.delete(self.get_cache_key(str(request.user.id), 'check'))
            cache.delete(self.get_cache_key(str(request.user.id), 'stats'))
        
        return Response({
            'status': 'success',
            'message': 'Resume deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)
    
    # ============================================================
    # 6. GET /api/resumes/current/ - Get current user's resume
    # ============================================================
    @action(detail=False, methods=['get'])
    def current(self, request):
        """
        Get the current user's resume.
        """
        resume = self.get_user_resume()
        
        if resume:
            serializer = self.get_serializer(resume)
            return Response({
                'status': 'success',
                'data': serializer.data
            })
        
        return Response({
            'status': 'success',
            'data': None,
            'message': 'No resume found'
        }, status=status.HTTP_200_OK)
    
    # ============================================================
    # 7. GET /api/resumes/check/ - Check if user has a resume
    # ============================================================
    @action(detail=False, methods=['get'])
    def check(self, request):
        """
        Check if the current user has a resume uploaded.
        """
        user_id = str(request.user.id)
        cache_key = self.get_cache_key(user_id, 'check')
        
        # Try cache first
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response({
                'status': 'success',
                'data': cached_data
            })
        
        resume = self.get_user_resume()
        
        data = {
            'has_resume': resume is not None,
            'resume_id': str(resume.id) if resume else None,
            'resume_name': resume.name if resume else None,
            'is_parsed': resume.is_parsed if resume else False,
            'is_processed': resume.is_processed if resume else False,
            'is_default': resume.is_default if resume else False,
            'supabase_url': resume.supabase_url if resume else None,
        }
        
        # Cache for 1 minute
        cache.set(cache_key, data, 60)
        
        return Response({
            'status': 'success',
            'data': data
        })
    
    # ============================================================
    # 8. GET /api/resumes/stats/ - Get resume statistics
    # ============================================================
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get statistics about the user's resume.
        """
        user_id = str(request.user.id)
        cache_key = self.get_cache_key(user_id, 'stats')
        
        # Try cache first
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response({
                'status': 'success',
                'data': cached_data
            })
        
        resume = self.get_user_resume()
        
        if not resume:
            data = {
                'has_resume': False,
                'message': 'No resume uploaded'
            }
            cache.set(cache_key, data, 60)
            return Response({
                'status': 'success',
                'data': data
            })
        
        stats = {
            'has_resume': True,
            'resume_id': str(resume.id),
            'name': resume.name,
            'file_size': resume.file_size,
            'file_size_mb': round(resume.file_size / (1024 * 1024), 2),
            'file_type': resume.file_type,
            'supabase_url': resume.supabase_url,
            'version': resume.version,
            'is_default': resume.is_default,
            'is_tailored': resume.is_tailored,
            'is_parsed': resume.is_parsed,
            'is_processed': resume.is_processed,
            'uploaded_at': resume.uploaded_at,
            'parsed_at': resume.parsed_at,
            'processed_at': resume.processed_at,
            'updated_at': resume.updated_at,
            'skills_count': len(resume.extracted_skills),
            'experience_years': resume.extracted_experience,
            'job_titles': resume.extracted_job_titles,
            'education_count': len(resume.extracted_education),
            'certifications_count': len(resume.extracted_certifications),
            'has_ats_score': resume.ats_score is not None,
            'ats_score': resume.ats_score,
            'tailored_versions_count': resume.tailored_versions.count(),
            'total_versions': resume.versions.count(),
            'supabase_bucket': resume.supabase_bucket,
            'supabase_path': resume.supabase_path,
        }
        
        # Cache for 5 minutes
        cache.set(cache_key, stats, 300)
        
        return Response({
            'status': 'success',
            'data': stats
        })
    
    # ============================================================
    # 9. POST /api/resumes/{id}/tailor/ - Tailor resume for job
    # ============================================================
    @action(detail=True, methods=['post'])
    def tailor(self, request, pk=None):
        """
        Tailor the resume for a specific job using AI.
        """
        resume = self.get_object()
        
        tailor_serializer = ResumeTailorSerializer(data=request.data)
        if not tailor_serializer.is_valid():
            return Response({
                'status': 'error',
                'errors': tailor_serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        job_id = tailor_serializer.validated_data['job_id']
        
        # Start tailoring task
        task = tailor_resume_async.delay(str(resume.id), job_id)
        
        return Response({
            'status': 'success',
            'task_id': task.id,
            'message': 'Resume tailoring started. This may take a few minutes.',
            'resume_id': str(resume.id)
        }, status=status.HTTP_202_ACCEPTED)
    
    # ============================================================
    # 10. POST /api/resumes/{id}/parse/ - Parse resume manually
    # ============================================================
    @action(detail=True, methods=['post'])
    def parse(self, request, pk=None):
        """
        Manually trigger parsing of the resume.
        """
        resume = self.get_object()
        
        # Trigger parsing
        task = parse_resume_async.delay(str(resume.id))
        
        return Response({
            'status': 'success',
            'task_id': task.id,
            'message': 'Resume parsing started'
        }, status=status.HTTP_202_ACCEPTED)
    
    # ============================================================
    # 11. GET /api/resumes/{id}/download/ - Download resume file
    # ============================================================
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """
        Download the resume file from Supabase.
        """
        resume = self.get_object()
        
        storage_service = ResumeStorageService()
        
        try:
            # Download from Supabase
            file_content = storage_service.download_resume(resume.supabase_path)
            
            # Create response
            response = HttpResponse(file_content, content_type=resume.file_type)
            response['Content-Disposition'] = f'attachment; filename="{resume.name}"'
            response['Content-Length'] = len(file_content)
            
            return response
            
        except Exception as e:
            logger.error(f"Resume download error: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Failed to download resume file'
            }, status=status.HTTP_404_NOT_FOUND)
    
    # ============================================================
    # 12. GET /api/resumes/{id}/versions/ - Get resume versions
    # ============================================================
    @action(detail=True, methods=['get'])
    def versions(self, request, pk=None):
        """
        Get all versions of a resume.
        """
        resume = self.get_object()
        versions = ResumeVersion.objects.filter(resume=resume)
        serializer = ResumeVersionSerializer(versions, many=True)
        
        return Response({
            'status': 'success',
            'data': serializer.data,
            'count': versions.count()
        })

    
    
    # ============================================================
    # 13. POST /api/resumes/{id}/set_default/ - Set as default
    # ============================================================
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """
        Set this resume as the default resume for the user.
        """
        resume = self.get_object()
        
        with transaction.atomic():
            # Unset default for all resumes
            Resume.objects.filter(user=request.user, is_default=True).update(is_default=False)
            
            # Set this resume as default
            resume.is_default = True
            resume.save()
            
            # Clear cache
            cache.delete(self.get_cache_key(str(request.user.id), 'data'))
            cache.delete(self.get_cache_key(str(request.user.id), 'check'))
            cache.delete(self.get_cache_key(str(request.user.id), 'stats'))
        
        return Response({
            'status': 'success',
            'message': 'Resume set as default',
            'data': {
                'id': str(resume.id),
                'name': resume.name,
                'is_default': True
            }
        })
    
    # ============================================================
    # 14. POST /api/resumes/bulk-delete/ - Delete multiple resumes
    # ============================================================
    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        """
        Delete multiple resumes at once.
        """
        delete_serializer = ResumeDeleteSerializer(data=request.data)
        if not delete_serializer.is_valid():
            return Response({
                'status': 'error',
                'errors': delete_serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        resume_ids = delete_serializer.validated_data['resume_ids']
        
        # Get resumes that belong to the user
        resumes = Resume.objects.filter(
            user=request.user,
            id__in=resume_ids
        )
        
        deleted_count = resumes.count()
        
        storage_service = ResumeStorageService()
        
        with transaction.atomic():
            for resume in resumes:
                # Delete from Supabase
                storage_service.delete_resume(
                    str(request.user.id),
                    resume.supabase_path
                )
                
                # Delete versions
                ResumeVersion.objects.filter(resume=resume).delete()
            
            # Delete resumes
            resumes.delete()
            
            # Clear cache
            cache.delete(self.get_cache_key(str(request.user.id), 'data'))
            cache.delete(self.get_cache_key(str(request.user.id), 'check'))
            cache.delete(self.get_cache_key(str(request.user.id), 'stats'))
        
        return Response({
            'status': 'success',
            'message': f'Deleted {deleted_count} resumes',
            'deleted_count': deleted_count
        })
    
    # ============================================================
    # 15. GET /api/resumes/search/ - Search resumes (admin only)
    # ============================================================
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Search resumes (admin only).
        """
        if not request.user.is_staff:
            return Response({
                'status': 'error',
                'message': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)
        
        query = request.query_params.get('q', '')
        
        if not query:
            return Response({
                'status': 'error',
                'message': 'Search query required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        resumes = Resume.objects.filter(
            Q(name__icontains=query) |
            Q(user__email__icontains=query) |
            Q(user__name__icontains=query) |
            Q(extracted_skills__icontains=query) |
            Q(parsed_text__icontains=query)
        ).select_related('user')[:50]
        
        serializer = self.get_serializer(resumes, many=True)
        
        return Response({
            'status': 'success',
            'data': serializer.data,
            'count': resumes.count()
        })
    
    # ============================================================
    # 16. GET /api/resumes/{id}/supabase-url/ - Get Supabase URL
    # ============================================================
    @action(detail=True, methods=['get'])
    def supabase_url(self, request, pk=None):
        """
        Get the Supabase public URL of the resume.
        """
        resume = self.get_object()
        
        return Response({
            'status': 'success',
            'data': {
                'id': str(resume.id),
                'supabase_url': resume.supabase_url,
                'supabase_path': resume.supabase_path,
                'supabase_bucket': resume.supabase_bucket
            }
        })
    
    # ============================================================
    # 17. POST /api/resumes/{id}/copy-for-edit/ - Copy resume for editing
    # ============================================================
    @action(detail=True, methods=['post'])
    def copy_for_edit(self, request, pk=None):
        """
        Copy the main resume's parsed_text into a new TailoredResume record
        for editing. The user can then edit the text and save it as a PDF.
        """
        resume = self.get_object()
        
        # Check if resume has parsed text
        if not resume.parsed_text:
            return Response({
                'status': 'error',
                'message': 'Resume has no parsed text. Wait for parsing to complete first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create a TailoredResume with the parsed text
        tailored = TailoredResume.objects.create(
            user=request.user,
            original_resume=resume,
            name=f"Copy of {resume.name}",
            tailored_text=resume.parsed_text,
            changes_summary={'action': 'copied_for_edit'},
            keywords_added=[],
            supabase_url='',
            supabase_path='',
            supabase_bucket=TailoredResume.TAILORED_BUCKET,
            file_size=0,
            file_type='text/plain',
        )
        
        serializer = TailoredResumeSerializer(tailored)
        
        return Response({
            'status': 'success',
            'message': 'Resume copied for editing. Edit the text and save when ready.',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)


class TailoredResumeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing TailoredResumes.
    Provides save-edited action for updating the tailored text and generating a PDF.
    """
    serializer_class = TailoredResumeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get tailored resumes for the current user"""
        return TailoredResume.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['put'], parser_classes=[JSONParser])
    def save_edited(self, request, pk=None):
        """
        Save edited tailored resume text.
        Generates a PDF from the edited text, uploads to Supabase 'Tailored resume' bucket,
        and updates the TailoredResume record with file info.
        """
        tailored = self.get_object()
        
        serializer = TailoredResumeEditSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        edited_text = serializer.validated_data['tailored_text']
        
        try:
            storage = ResumeStorageService()
            
            # Build a clean filename
            safe_name = "".join(c if c.isalnum() or c in ' -_' else '_' for c in tailored.get_filename())[:30]
            filename = f"{safe_name}_edited.pdf"
            
            # Generate PDF bytes
            pdf_bytes = PDFGenerator.generate_resume_pdf(
                resume_text=edited_text,
                title=f"Tailored Resume - {tailored.name}"
            )
            
            # Upload to 'Tailored resume' bucket
            upload_result = storage.upload_bytes(
                bucket_name=TailoredResume.TAILORED_BUCKET,
                user_id=str(request.user.id),
                file_bytes=pdf_bytes,
                filename=filename,
                content_type='application/pdf'
            )
            
            # Update the TailoredResume record
            tailored.tailored_text = edited_text
            tailored.supabase_url = upload_result['public_url']
            tailored.supabase_path = upload_result['path']
            tailored.supabase_bucket = upload_result['bucket']
            tailored.file_size = upload_result['file_size']
            tailored.file_type = upload_result['content_type']
            tailored.save()
            
            output_serializer = TailoredResumeSerializer(tailored)
            
            return Response({
                'status': 'success',
                'message': 'Tailored resume saved and PDF uploaded to Supabase.',
                'data': output_serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"❌ Save edited resume error: {str(e)}")
            return Response({
                'status': 'error',
                'message': f'Failed to save edited resume: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

