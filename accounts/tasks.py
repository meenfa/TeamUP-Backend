from celery import shared_task
from django.utils import timezone

from .models import Profile


@shared_task
def clear_expired_restrictions_task():
    # Beat can run this periodically so temporary bans are removed automatically.
    return Profile.objects.filter(is_temporarily_restricted=True, restricted_until__lte=timezone.now()).update(
        is_temporarily_restricted=False,
        restricted_until=None,
    )
