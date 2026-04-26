from django.db import models


class SkillLevel(models.TextChoices):
    BEGINNER = 'beginner', 'Beginner'
    INTERMEDIATE = 'intermediate', 'Intermediate'
    ADVANCED = 'advanced', 'Advanced'
    MIXED = 'mixed', 'Mixed'


class NotificationType(models.TextChoices):
    OTP = 'otp', 'OTP'
    GAME_REMINDER = 'game_reminder', 'Game Reminder'
    JOIN_CONFIRMATION = 'join_confirmation', 'Join Confirmation'
    SYSTEM = 'system', 'System'


class ParticipantStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    CONFIRMED = 'confirmed', 'Confirmed'
    CANCELLED = 'cancelled', 'Cancelled'
    ATTENDED = 'attended', 'Attended'
    NO_SHOW = 'no_show', 'No Show'
    REMOVED = 'removed', 'Removed'


class GameStatus(models.TextChoices):
    OPEN = 'open', 'Open'
    FULL = 'full', 'Full'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'
