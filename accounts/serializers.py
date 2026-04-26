from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Profile, User
from .services import EmailVerificationService, ReliabilityService


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ('email', 'phone_number', 'full_name', 'password')

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        EmailVerificationService.send_verification_email(user, enforce_cooldown=False)
        return user


class VerifyEmailSerializer(serializers.Serializer):
    token = serializers.CharField()

    def save(self, **kwargs):
        return EmailVerificationService.verify_email(token=self.validated_data['token'])


class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        user = User.objects.filter(email=value).first()
        if not user:
            raise serializers.ValidationError('User not found.')
        if user.is_verified:
            raise serializers.ValidationError('Account is already verified.')
        return value

    def save(self, **kwargs):
        user = User.objects.get(email=self.validated_data['email'])
        return EmailVerificationService.resend_verification_email(user)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(email=attrs['email'], password=attrs['password'])
        if not user:
            raise serializers.ValidationError('Invalid credentials.')
        if not user.is_verified:
            raise serializers.ValidationError('Account is not verified.')
        attrs['user'] = user
        return attrs

    def create_token_payload(self):
        user = self.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
        }


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def save(self, **kwargs):
        refresh = RefreshToken(self.validated_data['refresh'])
        refresh.blacklist()


class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    full_name = serializers.CharField(source='user.full_name', read_only=True)
    phone_number = serializers.CharField(source='user.phone_number', read_only=True)

    class Meta:
        model = Profile
        fields = (
            'email',
            'full_name',
            'phone_number',
            'city',
            'preferred_area',
            'skill_level',
            'bio',
            'reliability_score',
            'games_played',
            'no_show_count',
            'average_reliability_rating',
            'average_skill_honesty_rating',
            'is_temporarily_restricted',
            'restricted_until',
        )
        read_only_fields = (
            'reliability_score',
            'games_played',
            'no_show_count',
            'average_reliability_rating',
            'average_skill_honesty_rating',
            'is_temporarily_restricted',
            'restricted_until',
        )


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'phone_number', 'full_name', 'is_verified', 'profile')
