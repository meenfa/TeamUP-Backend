from datetime import timedelta
from decimal import Decimal
import random
import string

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from common.constants import SkillLevel

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, db_index=True)
    phone_number = models.CharField(max_length=20, unique=True, null=True, blank=True, db_index=True)
    full_name = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    verification_email_sent_at = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    objects = UserManager()

    class Meta:
        ordering = ('-date_joined',)

    def __str__(self):
        return self.email


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    city = models.CharField(max_length=120, blank=True)
    preferred_area = models.CharField(max_length=120, blank=True)
    skill_level = models.CharField(max_length=20, choices=SkillLevel.choices, default=SkillLevel.MIXED)
    bio = models.TextField(blank=True)
    reliability_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('100.00'))
    games_played = models.PositiveIntegerField(default=0)
    no_show_count = models.PositiveIntegerField(default=0)
    average_reliability_rating = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('0.00'))
    average_skill_honesty_rating = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('0.00'))
    is_temporarily_restricted = models.BooleanField(default=False)
    restricted_until = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-updated_at',)

    def __str__(self):
        return f'Profile<{self.user.email}>'

    def restriction_active(self):
        return bool(self.restricted_until and self.restricted_until > timezone.now())


class OTPPurpose(models.TextChoices):
    REGISTRATION = 'registration', 'Registration'
    LOGIN = 'login', 'Login'


class OTP(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='otps')
    code = models.CharField(max_length=10)
    purpose = models.CharField(max_length=20, choices=OTPPurpose.choices, default=OTPPurpose.REGISTRATION)
    sent_to = models.CharField(max_length=255)
    expires_at = models.DateTimeField()
    verified_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    attempts = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'purpose', 'is_active']),
            models.Index(fields=['sent_to', 'purpose', 'is_active']),
        ]
        ordering = ('-created_at',)

    def __str__(self):
        return f'OTP<{self.user.email}:{self.purpose}>'

    @staticmethod
    def generate_code(length: int = None) -> str:
        length = length or 6
        return ''.join(random.choices(string.digits, k=length))

    @classmethod
    def issue(cls, user, purpose, sent_to):
        cls.objects.filter(user=user, purpose=purpose, is_active=True).update(is_active=False)
        return cls.objects.create(
            user=user,
            purpose=purpose,
            sent_to=sent_to,
            code=cls.generate_code(),
            expires_at=timezone.now() + timedelta(minutes=10),
        )

    def is_expired(self):
        return timezone.now() >= self.expires_at


class NoShowRestriction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='restrictions')
    reason = models.CharField(max_length=255)
    starts_at = models.DateTimeField(default=timezone.now)
    ends_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['user', 'is_active', 'ends_at'])]
        ordering = ('-created_at',)

    def __str__(self):
        return f'Restriction<{self.user.email}>'
