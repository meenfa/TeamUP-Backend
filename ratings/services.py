from django.db.models import Avg

from accounts.models import Profile

from .models import Rating


class RatingService:
    @staticmethod
    def refresh_profile_aggregates(user):
        aggregates = Rating.objects.filter(to_user=user).aggregate(
            avg_reliability=Avg('reliability'),
            avg_skill_honesty=Avg('skill_honesty'),
        )
        profile = Profile.objects.get(user=user)
        profile.average_reliability_rating = aggregates['avg_reliability'] or 0
        profile.average_skill_honesty_rating = aggregates['avg_skill_honesty'] or 0
        profile.save(update_fields=['average_reliability_rating', 'average_skill_honesty_rating'])
        return profile
