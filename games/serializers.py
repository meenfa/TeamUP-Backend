from rest_framework import serializers

from accounts.serializers import UserSerializer
from common.constants import ParticipantStatus

from .models import Game, GameParticipant


class GameParticipantSerializer(serializers.ModelSerializer):
    # Nested serialization
    user = UserSerializer(read_only=True)

    class Meta:
        model = GameParticipant
        fields = ('id', 'user', 'status', 'joined_at', 'attendance_confirmed_at', 'removed_by_host')


class GameSerializer(serializers.ModelSerializer):
    host = UserSerializer(read_only=True)
    participants = GameParticipantSerializer(read_only=True, many=True)
    available_slots = serializers.IntegerField(read_only=True)
    host_reliability_score = serializers.DecimalField(source='host.profile.reliability_score', max_digits=5, decimal_places=2, read_only=True)

    class Meta:
        model = Game
        fields = (
            'id',
            'host',
            'location_name',
            'area_city',
            'game_date',
            'start_time',
            'end_time',
            'total_players',
            'skill_level',
            'entry_fee',
            'payment_note',
            'description',
            'status',
            'available_slots',
            'host_reliability_score',
            'participants',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('status',)

    def validate(self, attrs):
        if attrs['end_time'] <= attrs['start_time']:
            raise serializers.ValidationError('End time must be after start time.')
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        return Game.objects.create(host=user, **validated_data)


class AttendanceConfirmationSerializer(serializers.Serializer):
    pass


class ParticipantDecisionSerializer(serializers.Serializer):
    participant_user_id = serializers.IntegerField()


class MarkParticipantStatusSerializer(serializers.Serializer):
    participant_user_id = serializers.IntegerField()
    status = serializers.ChoiceField(choices=[ParticipantStatus.ATTENDED, ParticipantStatus.NO_SHOW, ParticipantStatus.REMOVED])
