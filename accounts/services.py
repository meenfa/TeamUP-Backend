from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core import signing
from django.db import transaction
from django.utils import timezone

from notifications.tasks import send_verification_email_task
from notifications.utils import safe_dispatch

from .models import NoShowRestriction, Profile, User
from .verification import build_email_verification_token, build_email_verification_url, load_email_verification_token


class EmailVerificationService:
    @staticmethod
    def send_verification_email(user: User, *, enforce_cooldown: bool = True):
        if user.is_verified:
            raise ValueError('Account is already verified.')
        if enforce_cooldown and user.verification_email_sent_at:
            elapsed = (timezone.now() - user.verification_email_sent_at).total_seconds()
            if elapsed < settings.EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS:
                raise ValueError('Please wait before requesting another verification email.')

        token = build_email_verification_token(user)
        verification_url = build_email_verification_url(token)
        user.verification_email_sent_at = timezone.now()
        user.save(update_fields=['verification_email_sent_at'])

        # Delivery is queued asynchronously so registration response stays fast.
        safe_dispatch(send_verification_email_task, user.id, user.email, user.full_name, verification_url)
        return verification_url

    @staticmethod
    def resend_verification_email(user: User):
        return EmailVerificationService.send_verification_email(user)

    @staticmethod
    @transaction.atomic
    def verify_email(token: str):
        try:
            payload = load_email_verification_token(token)
        except signing.SignatureExpired as exc:
            raise ValueError('Verification link has expired.') from exc
        except signing.BadSignature as exc:
            raise ValueError('Verification link is invalid.') from exc

        user = User.objects.select_for_update().filter(id=payload['user_id'], email=payload['email']).first()
        if not user:
            raise ValueError('User not found.')
        if user.is_verified:
            return user

        user.is_verified = True
        user.save(update_fields=['is_verified'])
        return user


class ReliabilityService:
    BASE_SCORE = Decimal('100.00')
    NO_SHOW_PENALTY = Decimal('12.50')
    ATTENDANCE_REWARD = Decimal('1.50')
    MIN_SCORE = Decimal('0.00')
    MAX_SCORE = Decimal('100.00')
    RESTRICTION_THRESHOLD = 3
    RESTRICTION_DAYS = 14

    @classmethod
    @transaction.atomic
    def apply_attendance_result(cls, user: User, attended: bool):
        profile = Profile.objects.select_for_update().get(user=user)

        # This score is intentionally simple for MVP transparency:
        # - attending rewards the user slightly
        # - no-shows apply a meaningful penalty
        # - score always stays between 0 and 100
        profile.games_played += 1
        if attended:
            profile.reliability_score = min(cls.MAX_SCORE, profile.reliability_score + cls.ATTENDANCE_REWARD)
        else:
            profile.no_show_count += 1
            profile.reliability_score = max(cls.MIN_SCORE, profile.reliability_score - cls.NO_SHOW_PENALTY)

        if profile.no_show_count >= cls.RESTRICTION_THRESHOLD:
            profile.is_temporarily_restricted = True
            profile.restricted_until = timezone.now() + timedelta(days=cls.RESTRICTION_DAYS)
            NoShowRestriction.objects.create(
                user=user,
                reason='Automatic restriction after repeated no-shows.',
                ends_at=profile.restricted_until,
            )

        profile.save()
        return profile

    @staticmethod
    def clear_expired_restriction_if_needed(profile: Profile):
        if profile.is_temporarily_restricted and profile.restricted_until and profile.restricted_until <= timezone.now():
            profile.is_temporarily_restricted = False
            profile.restricted_until = None
            profile.save(update_fields=['is_temporarily_restricted', 'restricted_until'])
        return profile
