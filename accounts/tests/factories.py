import factory
from factory.django import DjangoModelFactory
from decimal import Decimal
from django.utils import timezone
from accounts.models import User, Profile, NoShowRestriction

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
    
    email = factory.Sequence(lambda n: f'testuser{n}@example.com')
    full_name = "Test User"
    google_sub = factory.Sequence(lambda n: f'google_test_{n}')
    is_active = True
    is_verified = True
    
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Create user with properly hashed password"""
        password = kwargs.pop('password', 'testpass123')
        user = model_class(*args, **kwargs)
        user.set_password(password)
        user.save()
        return user


class ProfileFactory(DjangoModelFactory):
    """Factory for creating test profiles"""
    class Meta:
        model = Profile
    
    user = factory.SubFactory(UserFactory)
    bio = factory.Faker('text', max_nb_chars=200)
    city = factory.Faker('city')
    skill_level = 'mixed'
    reliability_score = Decimal('100.00')
    games_played = 0
    no_show_count = 0
    average_reliability_rating = Decimal('0.00')
    average_skill_honesty_rating = Decimal('0.00')
    is_temporarily_restricted = False
    restricted_until = None


class NoShowRestrictionFactory(DjangoModelFactory):
    """Factory for creating no-show restrictions"""
    class Meta:
        model = NoShowRestriction
    
    user = factory.SubFactory(UserFactory)
    reason = "Test restriction reason"
    ends_at = factory.Faker('date_time_between', start='+1d', end='+30d')
    is_active = True