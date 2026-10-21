# backend/django_app/users/serializers.py
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from .models import User, Education, Experience, Project, Certification, Language


# ============================================================
# Education Serializer
# ============================================================
class EducationSerializer(serializers.ModelSerializer):
    """Education serialization"""
    
    duration = serializers.SerializerMethodField()
    duration_years = serializers.SerializerMethodField()
    
    class Meta:
        model = Education
        fields = [
            'id', 'institution_name', 'institution_location', 'institution_logo',
            'degree_type', 'degree_name', 'major', 'minor',
            'grade_type', 'obtained_marks', 'max_marks', 'grade_scale',
            'start_date', 'end_date', 'is_current',
            'description', 'achievements', 'courses', 'activities',
            'order', 'duration', 'duration_years',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_duration(self, obj):
        return obj.get_duration()
    
    def get_duration_years(self, obj):
        return obj.get_duration() / 12 if obj.get_duration() > 0 else 0


class EducationCreateUpdateSerializer(serializers.ModelSerializer):
    """Education create/update serializer"""
    
    class Meta:
        model = Education
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def validate(self, data):
        if data.get('is_current') and data.get('end_date'):
            raise serializers.ValidationError({
                'end_date': 'End date should not be set for current education'
            })
        if not data.get('is_current') and not data.get('end_date'):
            raise serializers.ValidationError({
                'end_date': 'End date is required for completed education'
            })
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError({
                    'end_date': 'End date must be after start date'
                })
        return data


# ============================================================
# Experience Serializer
# ============================================================
class ExperienceSerializer(serializers.ModelSerializer):
    """Experience serialization"""
    
    duration = serializers.SerializerMethodField()
    duration_years = serializers.SerializerMethodField()
    
    class Meta:
        model = Experience
        fields = [
            'id', 'company_name', 'company_location', 'company_website', 
            'company_logo', 'company_industry',
            'job_title', 'employment_type', 'experience_level',
            'start_date', 'end_date', 'is_current',
            'description', 'achievements', 'technologies_used', 'skills_used',
            'order', 'duration', 'duration_years',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_duration(self, obj):
        return obj.get_duration()
    
    def get_duration_years(self, obj):
        return obj.get_duration_years()


class ExperienceCreateUpdateSerializer(serializers.ModelSerializer):
    """Experience create/update serializer"""
    
    class Meta:
        model = Experience
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def validate(self, data):
        if data.get('is_current') and data.get('end_date'):
            raise serializers.ValidationError({
                'end_date': 'End date should not be set for current experience'
            })
        if not data.get('is_current') and not data.get('end_date'):
            raise serializers.ValidationError({
                'end_date': 'End date is required for completed experience'
            })
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError({
                    'end_date': 'End date must be after start date'
                })
        return data


# ============================================================
# Project Serializer
# ============================================================
class ProjectSerializer(serializers.ModelSerializer):
    """Project serialization"""
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'project_type', 'status',
            'description', 'long_description',
            'technologies', 'skills_used',
            'project_url', 'github_url', 'demo_url',
            'cover_image', 'screenshots',
            'start_date', 'end_date', 'is_current',
            'team_size', 'team_members', 'role',
            'achievements', 'challenges', 'learnings',
            'order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProjectCreateUpdateSerializer(serializers.ModelSerializer):
    """Project create/update serializer"""
    
    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def validate(self, data):
        if data.get('is_current') and data.get('end_date'):
            raise serializers.ValidationError({
                'end_date': 'End date should not be set for current project'
            })
        if not data.get('is_current') and not data.get('end_date'):
            raise serializers.ValidationError({
                'end_date': 'End date is required for completed project'
            })
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError({
                    'end_date': 'End date must be after start date'
                })
        return data


# ============================================================
# Certification Serializer
# ============================================================
class CertificationSerializer(serializers.ModelSerializer):
    """Certification serialization"""
    
    is_valid = serializers.SerializerMethodField()
    
    class Meta:
        model = Certification
        fields = [
            'id', 'name', 'issuing_organization', 'level',
            'credential_id', 'credential_url', 'verification_url',
            'issue_date', 'expiry_date', 'is_lifetime', 'is_expired',
            'skills_covered', 'description', 'order',
            'is_valid', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_is_valid(self, obj):
        return obj.is_valid()


class CertificationCreateUpdateSerializer(serializers.ModelSerializer):
    """Certification create/update serializer"""
    
    class Meta:
        model = Certification
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def validate(self, data):
        if data.get('is_lifetime') and data.get('expiry_date'):
            raise serializers.ValidationError({
                'expiry_date': 'Expiry date should not be set for lifetime certification'
            })
        if not data.get('is_lifetime') and not data.get('expiry_date'):
            raise serializers.ValidationError({
                'expiry_date': 'Expiry date is required for non-lifetime certification'
            })
        if data.get('issue_date') and data.get('expiry_date'):
            if data['issue_date'] > data['expiry_date']:
                raise serializers.ValidationError({
                    'expiry_date': 'Expiry date must be after issue date'
                })
        return data


# ============================================================
# Language Serializer
# ============================================================
class LanguageSerializer(serializers.ModelSerializer):
    """Language serialization"""
    
    class Meta:
        model = Language
        fields = [
            'id', 'name', 'proficiency', 'is_native',
            'order', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


# ============================================================
# User Serializers
# ============================================================
class UserProfileSerializer(serializers.ModelSerializer):
    """Complete user profile serialization with all sections"""
    
    educations = EducationSerializer(many=True, read_only=True)
    experiences = ExperienceSerializer(many=True, read_only=True)
    projects = ProjectSerializer(many=True, read_only=True)
    certifications = CertificationSerializer(many=True, read_only=True)
    languages = LanguageSerializer(many=True, read_only=True)
    
    skills_display = serializers.SerializerMethodField()
    preferred_jobs_display = serializers.SerializerMethodField()
    preferred_locations_display = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'username',
            'name',
            'phone',
            'dob',
            'address',
            'gender',
            'profile_picture',
            'bio',
            'skills',
            'skills_display',
            'preferred_job_titles',
            'preferred_jobs_display',
            'preferred_locations',
            'preferred_locations_display',
            'professional_summary',
            'linkedin_url',
            'github_url',
            'portfolio_url',
            'educations',
            'experiences',
            'projects',
            'certifications',
            'languages',
            'is_active',
            'is_verified',
            'email_verified',
            'preferences',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    
    def get_skills_display(self, obj):
        return obj.get_skills_list()
    
    def get_preferred_jobs_display(self, obj):
        return obj.get_preferred_jobs()
    
    def get_preferred_locations_display(self, obj):
        return obj.get_preferred_locations()


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """User profile update serializer"""
    
    class Meta:
        model = User
        fields = [
            'name',
            'phone',
            'dob',
            'address',
            'gender',
            'profile_picture',
            'bio',
            'skills',
            'preferred_job_titles',
            'preferred_locations',
            'professional_summary',
            'linkedin_url',
            'github_url',
            'portfolio_url',
            'preferences',
        ]
    
    
    def update(self, instance, validated_data):
        # Ensure skills is a list
        if 'skills' in validated_data and not isinstance(validated_data['skills'], list):
            validated_data['skills'] = []
        
        # Ensure preferred_job_titles is a list
        if 'preferred_job_titles' in validated_data and not isinstance(validated_data['preferred_job_titles'], list):
            validated_data['preferred_job_titles'] = []
        
        # Ensure preferred_locations is a list
        if 'preferred_locations' in validated_data and not isinstance(validated_data['preferred_locations'], list):
            validated_data['preferred_locations'] = []
        
        return super().update(instance, validated_data)


class UserPreferencesSerializer(serializers.Serializer):
    """User preferences validation and serialization"""
    
    # Job preferences
    job_titles = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=[]
    )
    locations = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=[]
    )
    
    # Company preferences
    company_types = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=[]
    )
    industries = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=[]
    )
    
    # Salary preferences
    salary_min = serializers.FloatField(required=False, min_value=0)
    salary_max = serializers.FloatField(required=False, min_value=0)
    
    # Job search settings
    max_jobs_per_search = serializers.IntegerField(required=False, min_value=10, max_value=200, default=50)
    min_match_score = serializers.IntegerField(required=False, min_value=0, max_value=100, default=60)
    
    # Sources
    sources = serializers.DictField(
        child=serializers.BooleanField(),
        required=False,
        default={'linkedin': True, 'indeed': True}
    )
    
    # Automation settings
    automation = serializers.DictField(
        child=serializers.BooleanField(),
        required=False,
        default={'auto_apply': False, 'auto_discover': True}
    )
    
    # Application pace
    application_pace = serializers.ChoiceField(
        choices=['conservative', 'moderate', 'aggressive'],
        default='moderate'
    )


class UserRegisterSerializer(serializers.ModelSerializer):
    """User registration serializer"""
    
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'name', 'phone', 'password', 'password2')
        read_only_fields = ('id',)
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT serializer with user data"""
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        data['user'] = {
            'id': str(self.user.id),
            'email': self.user.email,
            'name': self.user.name,
            'skills': self.user.skills,
            'preferred_job_titles': self.user.preferred_job_titles,
            'preferred_locations': self.user.preferred_locations,
            'preferences': self.user.preferences,
        }
        
        return data










