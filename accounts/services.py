from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from .models import NoShowRestriction, Profile, User

import uuid
from django.utils.text import slugify

import uuid
from django.db import transaction
from django.utils.text import slugify
from django.conf import settings

from rest_framework_simplejwt.tokens import RefreshToken

from .models import User

class GoogleAuthService:
    @staticmethod
    def _verify_id_token(token: str):
        if not settings.GOOGLE_OAUTH_CLIENT_ID:
            raise ValueError("GOOGLE_OAUTH_CLIENT_ID is not configured.")

        try:
            from google.auth.transport import requests as google_requests
            from google.oauth2 import id_token
        except ImportError as exc:
            raise ValueError("Google auth dependencies are not installed.") from exc

        try:
            return id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                settings.GOOGLE_OAUTH_CLIENT_ID,
            )
        except ValueError:
            raise ValueError("Invalid Google ID token.")

    # ---------------------------
    # username generator
    # ---------------------------
    @staticmethod
    def generate_username(full_name: str):
        base = slugify(full_name)[:20] or "user"
        unique_id = uuid.uuid4().hex[:6]
        return f"{base}-{unique_id}"

    # ---------------------------
    # main auth flow
    # ---------------------------
    @classmethod
    @transaction.atomic
    def authenticate(cls, token: str):
        payload = cls._verify_id_token(token)

        google_sub = payload.get("sub")
        email = payload.get("email")
        full_name = (payload.get("name") or "").strip()
        picture = payload.get("picture")

        if not google_sub:
            raise ValueError("Google token missing sub.")
        if not email:
            raise ValueError("Google token missing email.")
        if not payload.get("email_verified", False):
            raise ValueError("Google email not verified.")

        # ---------------------------
        # FIND USER
        # ---------------------------
        user = User.objects.select_for_update().filter(google_sub=google_sub).first()

        if user is None:
            user = User.objects.select_for_update().filter(email=email).first()

            if user and user.google_sub and user.google_sub != google_sub:
                raise ValueError("Email linked to another Google account.")

        # ---------------------------
        # CREATE USER
        # ---------------------------
        if user is None:
            user = User.objects.create_user(
                email=email,
                password=None,
                full_name=full_name or email.split("@")[0],
                google_sub=google_sub,
                is_verified=True,
            )

            # username
            user.username = cls.generate_username(user.full_name)
            user.save(update_fields=["username"])

        # ---------------------------
        # UPDATE USER
        # ---------------------------
        updated_fields = []

        if user.google_sub != google_sub:
            user.google_sub = google_sub
            updated_fields.append("google_sub")

        if user.email != email:
            user.email = email
            updated_fields.append("email")

        if full_name and user.full_name != full_name:
            user.full_name = full_name
            updated_fields.append("full_name")

        if not user.is_verified:
            user.is_verified = True
            updated_fields.append("is_verified")

        if not user.username:
            user.username = cls.generate_username(user.full_name)
            updated_fields.append("username")

        if updated_fields:
            user.save(update_fields=updated_fields)

        # ---------------------------
        # PROFILE PHOTO (Google fallback)
        # ---------------------------
        profile = user.profile

        if picture and not profile.google_photo:
            profile.google_photo = picture
            profile.save(update_fields=["google_photo"])

        return user

    # ---------------------------
    # token response
    # ---------------------------
    @staticmethod
    def create_token_payload(user: User):
        refresh = RefreshToken.for_user(user)

        from .serializers import UserSerializer

        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user).data,
        }

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
