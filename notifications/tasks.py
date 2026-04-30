import logging
from datetime import datetime, timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from common.constants import NotificationType

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def schedule_game_reminder_task(self, game_id: int, user_id: int):
    from games.models import Game
    from notifications.models import Notification

    try:
        game = Game.objects.get(id=game_id)
    except Game.DoesNotExist:
        logger.warning('Game %s not found for reminder scheduling.', game_id)
        return

    reminder_time = timezone.make_aware(datetime.combine(game.game_date, game.start_time)) - timedelta(minutes=settings.GAME_REMINDER_LEAD_MINUTES)
    if reminder_time <= timezone.now():
        Notification.objects.create(
            user_id=user_id,
            notification_type=NotificationType.GAME_REMINDER,
            title='Upcoming game reminder',
            message=f'Reminder: your game at {game.location_name} starts at {game.start_time}.',
        )
        return

    send_game_reminder_task.apply_async(args=[game_id, user_id], eta=reminder_time)


@shared_task(bind=True, max_retries=3)
def send_game_reminder_task(self, game_id: int, user_id: int):
    from games.models import Game
    from notifications.models import Notification

    try:
        game = Game.objects.get(id=game_id)
    except Game.DoesNotExist:
        logger.warning('Game %s not found for reminder.', game_id)
        return

    Notification.objects.create(
        user_id=user_id,
        notification_type=NotificationType.GAME_REMINDER,
        title='Upcoming game reminder',
        message=f'Your TeamUp game at {game.location_name} starts on {game.game_date} at {game.start_time}.',
    )
    logger.info('Game reminder created for user=%s game=%s', user_id, game_id)
