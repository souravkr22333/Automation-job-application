# backend/django_app/core/management/commands/create_admin.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

class Command(BaseCommand):
    help = 'Create an admin user if none exists'
    
    def handle(self, *args, **options):
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write('Admin user already exists')
            return
        
        email = 'admin@autoapply.ai'
        password = 'admin123'
        name = 'Admin'
        
        try:
            user = User.objects.create_superuser(
                username=email,
                email=email,
                password=password,
                name=name
            )
            self.stdout.write(
                self.style.SUCCESS(f'Admin user created: {email} / {password}')
            )
        except ValidationError as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to create admin: {str(e)}')
            )