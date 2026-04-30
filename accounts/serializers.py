from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Profile, User
from .services import GoogleAuthService

class GoogleAuthSerializer(serializers.Serializer):
    id_token = serializers.CharField(required=False, write_only=True)
    credential = serializers.CharField(required=False, write_only=True)

    def validate(self, attrs):
        token = attrs.get("id_token") or attrs.get("credential")

        if not token:
            raise serializers.ValidationError(
                {"token": "Provide either id_token or credential."}
            )

        return {"token": token}

    def save(self, **kwargs):
        """
        Authenticate or create user via Google token.
        Returns User instance.
        """
        user = GoogleAuthService.authenticate(
            self.validated_data["token"]
        )
        return user


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def save(self, **kwargs):
        refresh = RefreshToken(self.validated_data["refresh"])
        refresh.blacklist()

class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    full_name = serializers.CharField(source="user.full_name", required=False)
    phone_number = serializers.CharField(
        source="user.phone_number",
        required=False,
        allow_blank=True,
        allow_null=True
    )
    profile_photo = serializers.ImageField(required=False)
    google_photo = serializers.URLField(read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    
    display_photo = serializers.SerializerMethodField()
    class Meta:
        model = Profile
        fields = (
            "email",
            "full_name",
            "phone_number",
            "username",
            "profile_photo",
            "google_photo",
            "display_photo",
            "city",
            "preferred_area",
            "skill_level",
            "bio",
            "reliability_score",
            "games_played",
            "no_show_count",
            "average_reliability_rating",
            "average_skill_honesty_rating",
            "is_temporarily_restricted",
            "restricted_until",
        )
        read_only_fields = (
            "reliability_score",
            "games_played",
            "no_show_count",
            "average_reliability_rating",
            "average_skill_honesty_rating",
            "is_temporarily_restricted",
            "restricted_until",
        )

    def get_display_photo(self, obj):
        if obj.profile_photo:
            return obj.profile_photo.url
        return obj.google_photo
    
    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", None)
        user = instance.user

        if user_data:
            user.full_name = user_data.get("full_name", user.full_name)
            user.phone_number = user_data.get("phone_number", user.phone_number)
            user.save()

        return super().update(instance, validated_data)


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "phone_number",
            "full_name",
            "is_verified",
            "profile",
        )