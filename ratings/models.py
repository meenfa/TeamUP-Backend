from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from games.models import Game

import uuid

try:
    import uuid6
    default_uuid_generator = uuid6.uuid7
except ImportError:
    default_uuid_generator= uuid.uuid4


class Rating(models.Model):
    id=models.UUIDField(primary_key=True, default=default_uuid_generator, editable=False)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='ratings')
    from_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ratings_given')
    to_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ratings_received')
    reliability = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    skill_honesty = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('game', 'from_user', 'to_user')
        indexes = [
            models.Index(fields=['to_user', 'created_at']),
            models.Index(fields=['game', 'to_user']),
        ]
        ordering = ('-created_at',)

    def __str__(self):
        return f'Rating<{self.from_user_id}->{self.to_user_id}>'
