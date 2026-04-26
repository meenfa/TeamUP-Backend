import logging
import json
from datetime import datetime, timedelta
from urllib import error as urllib_error
from urllib import request as urllib_request

from celery import shared_task
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

from common.constants import NotificationType

logger = logging.getLogger(__name__)


def _send_resend_email(destination: str, subject: str, html: str):
    payload = json.dumps(
        {
            'from': settings.DEFAULT_FROM_EMAIL,
            'to': [destination],
            'subject': subject,
            'html': html,
        }
    ).encode('utf-8')
    request = urllib_request.Request(
        'https://api.resend.com/emails',
        data=payload,
        headers={
            'Authorization': f'Bearer {settings.RESEND_API_KEY}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )
    with urllib_request.urlopen(request, timeout=15) as response:
        body = json.loads(response.read().decode('utf-8') or '{}')
    return body.get('id')


@shared_task(bind=True, max_retries=3)
def send_verification_email_task(self, user_id: int, destination: str, full_name: str, verification_url: str):
    from notifications.models import Notification

    subject = 'Verify your TeamUp email'
    html = render_to_string(
        'notifications/email_verification_email.html',
        {
            'full_name': full_name,
            'verification_url': verification_url,
            'expiry_hours': max(settings.EMAIL_VERIFICATION_TOKEN_MAX_AGE_SECONDS // 3600, 1),
        },
    )

    if not settings.RESEND_API_KEY:
        Notification.objects.create(
            user_id=user_id,
            notification_type=NotificationType.SYSTEM,
            title='Verification email fallback',
            message=f'Resend is not configured. Use this verification link: {verification_url}',
        )
        logger.warning('RESEND_API_KEY is not configured. Verification link for %s: %s', destination, verification_url)
        return None

    try:
        email_id = _send_resend_email(destination, subject, html)
    except (urllib_error.HTTPError, urllib_error.URLError, TimeoutError, ValueError) as exc:
        Notification.objects.create(
            user_id=user_id,
            notification_type=NotificationType.SYSTEM,
            title='Verification email fallback',
            message=f'Resend delivery failed. Use this verification link: {verification_url}',
        )
        logger.exception('Failed to send verification email to %s via Resend. Link: %s', destination, verification_url)
        return None

    logger.info('Verification email sent to %s via Resend. Email id: %s', destination, email_id)
    return email_id


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
