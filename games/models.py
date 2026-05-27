from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from common.constants import GameStatus, ParticipantStatus, SkillLevel
import uuid

try:
    import uuid6
    default_uuid_generator = uuid6.uuid7
except ImportError:
    default_uuid_generator = uuid.uuid4
    
    
class Game(models.Model):
    id=models.UUIDField(primary_key=True, default=default_uuid_generator, editable=False)
    host = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='hosted_games')
    location_name = models.CharField(max_length=255)
    area_city = models.CharField(max_length=120, db_index=True)
    game_date = models.DateField(db_index=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    total_players = models.PositiveIntegerField(validators=[MinValueValidator(2)])
    skill_level = models.CharField(max_length=20, choices=SkillLevel.choices, default=SkillLevel.MIXED, db_index=True)
    entry_fee = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    payment_note = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=GameStatus.choices, default=GameStatus.OPEN, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('game_date', 'start_time')
        indexes = [
            models.Index(fields=['area_city', 'game_date', 'skill_level']),
            models.Index(fields=['status', 'game_date']),
        ]

    def __str__(self):
        return f'{self.location_name} - {self.game_date}'

    def clean(self):
        if self.end_time <= self.start_time:
            raise ValidationError('End time must be after start time.')

    @property
    def available_slots(self):
        # Host occupies one slot, so availability counts host + active participants.
        active_count = 1 + self.participants.exclude(status__in=[ParticipantStatus.CANCELLED, ParticipantStatus.REMOVED]).count()
        return max(self.total_players - active_count, 0)

    def refresh_status(self):
        if self.status in [GameStatus.CANCELLED, GameStatus.COMPLETED]:
            return self.status
        self.status = GameStatus.FULL if self.available_slots == 0 else GameStatus.OPEN
        self.save(update_fields=['status', 'updated_at'])
        return self.status

    def has_started(self):
        return timezone.now() >= timezone.make_aware(timezone.datetime.combine(self.game_date, self.start_time))


class GameParticipant(models.Model):
    id=models.UUIDField(primary_key=True, default=default_uuid_generator, editable=False)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='game_participations')
    status = models.CharField(max_length=20, choices=ParticipantStatus.choices, default=ParticipantStatus.PENDING, db_index=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    attendance_confirmed_at = models.DateTimeField(null=True, blank=True)
    removed_by_host = models.BooleanField(default=False)

    class Meta:
        unique_together = ('game', 'user')
        indexes = [
            models.Index(fields=['game', 'status']),
            models.Index(fields=['user', 'status']),
        ]
        ordering = ('joined_at',)

    def __str__(self):
        return f'{self.user.email} @ Game<{self.game_id}>'
