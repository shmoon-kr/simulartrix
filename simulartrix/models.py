from django.db import models
from django.db.models import Sum, Max
from django.core.validators import validate_email
from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin
from django_choices_field import IntegerChoicesField
from strawberry_django.descriptors import model_cached_property
from typing import List

# Create your models here.

class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, name, password, **extra_fields):
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

    def create_superuser(self, email, name, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, name, password, **extra_fields)


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
