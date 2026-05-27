from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from common.constants import SkillLevel

from .managers import UserManager
import uuid

try:
    import uuid6
    default_uuid_generator = uuid6.uuid7
except ImportError:
    default_uuid_generator= uuid.uuid4

class User(AbstractBaseUser, PermissionsMixin):
    id=models.UUIDField(primary_key=True, default=default_uuid_generator, editable=False)
    email = models.EmailField(unique=True)
    google_sub = models.CharField(max_length=255, unique=True, null=True, blank=True, db_index=True)
    phone_number = models.CharField(max_length=20, unique=True, null=True, blank=True, db_index=True)
    full_name = models.CharField(max_length=150)
    username = models.SlugField(unique=True, blank=True, null=True, db_index=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
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
    id=models.UUIDField(primary_key=True, default=default_uuid_generator, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    
    profile_photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True)
    google_photo = models.URLField(null=True, blank=True)
    
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


class NoShowRestriction(models.Model):
    id=models.UUIDField(primary_key=True, default=default_uuid_generator, editable=False)
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
