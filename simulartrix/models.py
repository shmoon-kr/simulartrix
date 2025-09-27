from django.db import models
from django.db.models import Sum, Max
from django.core.validators import validate_email
from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin
from django_choices_field import IntegerChoicesField
from strawberry_django.descriptors import model_cached_property
from typing import List

# Create your models here.

class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, name=None, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        validate_email(email)
        user = self.model(email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, name, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, name, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser, PermissionsMixin):
    """User model."""

    objects = UserManager()

    # from gqlauth.models import UserStatus

    email = models.EmailField(max_length=255, unique=True, verbose_name='이메일')
    name = models.CharField(max_length=20, null=True, blank=True, verbose_name='이름')
    first_name = last_name = None
    username = None

    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return str(self.email)


class SessionTemplate(models.Model):
    """Defines a base template for a simulation session."""

    name = models.CharField(max_length=100, unique=True, verbose_name='Template Name')
    description = models.TextField(blank=True, verbose_name='Template Description')

    system_prompt = models.TextField(verbose_name='System Prompt', help_text='LLM에게 제공할 베이스 시스템 프롬프트')

    base_image = models.ImageField(upload_to='template_images/', null=True, blank=True, verbose_name='Base Image')
    thumbnail = models.ImageField(upload_to='template_thumbnails/', null=True, blank=True,
                                  verbose_name='Thumbnail Image')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_public = models.BooleanField(default=False, help_text='다른 사용자에게 공개할 수 있는 템플릿인지 여부')

    def __str__(self):
        return self.name


class Session(models.Model):
    """LLM interaction session."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sessions')
    template = models.ForeignKey(SessionTemplate, on_delete=models.CASCADE, related_name='sessions')
    title = models.CharField(max_length=100, default='Untitled Session')
    system_prompt = models.TextField(default='You are a helpful assistant.')
    context_summary = models.TextField(blank=True, null=True, help_text='Summarized context for long-term memory')
    last_context_update = models.ForeignKey('Tick', blank=True, null=True, default=None, on_delete=models.CASCADE, related_name='+')
    is_active = models.BooleanField(default=False, help_text='현재 진행중인 Session인지 여부')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.email} - {self.title}'


class Tick(models.Model):
    """세션의 단일 틱."""
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='ticks')
    user_input = models.TextField(default='continue', blank=True, help_text="사용자가 입력한 명령 (없으면 None)")
    llm_response = models.TextField(help_text="LLM 응답")
    context_snapshot = models.TextField(help_text="이 틱 시점의 context 요약", blank=True)
    token_usage = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Tick {self.session} @ {self.create_at.strftime('%Y-%m-%d %H:%M:%S')}"
