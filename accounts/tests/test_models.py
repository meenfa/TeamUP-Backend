import pytest
from decimal import Decimal
from datetime import timedelta
from django.db import IntegrityError
from django.utils import timezone
from django.contrib.auth import get_user_model
from accounts.models import Profile, NoShowRestriction

User = get_user_model()
pytestmark = pytest.mark.django_db


class TestUserModel:
    """Core user creation and constraints"""
    
    def test_create_valid_user(self):
        """Minimal valid user creation"""
        user = User.objects.create_user(
            email='test@gmail.com',
            full_name='Test User',
            password='pass123'
        )
        assert user.email == 'test@gmail.com'
        assert user.check_password('pass123')
    
    def test_create_user_without_full_name_uses_default(self):
        """Your UserManager handles missing full_name gracefully"""
        # This should not raise an error - your manager provides a default
        user = User.objects.create_user(email='only@email.com')
        assert user.email == 'only@email.com'
        assert user.full_name is not None  # Your manager sets a default
    
    def test_unique_constraints(self):
        """Email, google_sub, phone_number must be unique"""
        User.objects.create_user(
            email='unique@gmail.com', 
            full_name='First', 
            password='pass'
        )
        
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                email='unique@gmail.com', 
                full_name='Second', 
                password='pass'
            )
    
    def test_superuser_has_admin_permissions(self):
        """Superuser creation works correctly"""
        admin = User.objects.create_superuser(
            email='admin@gmail.com', 
            full_name='Admin', 
            password='pass'
        )
        assert admin.is_staff and admin.is_superuser


class TestProfileModel:
    """Profile auto-creation and updates"""
    
    def test_profile_auto_created(self):
        """Profile created automatically with user"""
        user = User.objects.create_user(
            email='profile@gmail.com', 
            full_name='Profile User', 
            password='pass'
        )
        assert isinstance(user.profile, Profile)
        assert user.profile.reliability_score == Decimal('100.00')
    
    def test_profile_updates(self):
        """Profile fields can be updated"""
        user = User.objects.create_user(
            email='update@gmail.com', 
            full_name='Update User', 
            password='pass'
        )
        profile = user.profile
        
        profile.bio = "New bio"
        profile.city = "Boston"
        profile.save()
        
        profile.refresh_from_db()
        assert profile.bio == "New bio" 
        assert profile.city == "Boston"
    
    def test_restriction_logic(self):
        """restriction_active() method works correctly"""
        user = User.objects.create_user(
            email='restrict@gmail.com', 
            full_name='Restrict User', 
            password='pass'
        )
        profile = user.profile
        
        assert profile.restriction_active() is False
        
        profile.restricted_until = timezone.now() + timedelta(days=1)
        assert profile.restriction_active() is True
        
        profile.restricted_until = timezone.now() - timedelta(days=1)
        assert profile.restriction_active() is False
    
    def test_profile_deleted_with_user(self):
        """Cascade delete removes profile when user is deleted"""
        user = User.objects.create_user(
            email='cascade@gmail.com', 
            full_name='Cascade User', 
            password='pass'
        )
        profile_id = user.profile.id
        
        user.delete()
        
        with pytest.raises(Profile.DoesNotExist):
            Profile.objects.get(id=profile_id)


class TestNoShowRestrictionModel:
    """Restriction tracking and business rules"""
    
    def test_create_restriction(self):
        """Can create restriction for user"""
        user = User.objects.create_user(
            email='restriction@gmail.com', 
            full_name='Restrict User', 
            password='pass'
        )
        ends_at = timezone.now() + timedelta(days=14)
        
        restriction = NoShowRestriction.objects.create(
            user=user,
            reason='Test reason',
            ends_at=ends_at
        )
        
        assert restriction.user == user
        assert restriction.reason == 'Test reason'
        assert restriction.is_active is True
    
    def test_restriction_requires_end_date(self):
        """ends_at is required field"""
        user = User.objects.create_user(
            email='enddate@gmail.com', 
            full_name='End Date User', 
            password='pass'
        )
        
        with pytest.raises(IntegrityError):
            NoShowRestriction.objects.create(user=user, reason='No end date')
    
    def test_user_can_have_multiple_restrictions(self):
        """History of restrictions is preserved"""
        user = User.objects.create_user(
            email='multiple@gmail.com', 
            full_name='Multiple User', 
            password='pass'
        )
        
        NoShowRestriction.objects.create(
            user=user, 
            reason='First', 
            ends_at=timezone.now() + timedelta(days=7)
        )
        NoShowRestriction.objects.create(
            user=user, 
            reason='Second', 
            ends_at=timezone.now() + timedelta(days=14)
        )
        
        assert NoShowRestriction.objects.filter(user=user).count() == 2