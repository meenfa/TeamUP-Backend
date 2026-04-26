from rest_framework import serializers

from accounts.serializers import UserSerializer
from games.models import GameParticipant
from common.constants import ParticipantStatus

from .models import Rating
from .services import RatingService


class RatingSerializer(serializers.ModelSerializer):
    from_user = UserSerializer(read_only=True)
    to_user = UserSerializer(read_only=True)

    class Meta:
        model = Rating
        fields = ('id', 'game', 'from_user', 'to_user', 'reliability', 'skill_honesty', 'comment', 'created_at')
        read_only_fields = ('from_user', 'created_at')

    def validate(self, attrs):
        request = self.context['request']
        to_user = self.initial_data.get('to_user')
        game = attrs['game']
        if not to_user:
            raise serializers.ValidationError({'to_user': 'This field is required.'})
        if str(request.user.id) == str(to_user):
            raise serializers.ValidationError('Users cannot rate themselves.')
        if Rating.objects.filter(game=game, from_user=request.user, to_user_id=to_user).exists():
            raise serializers.ValidationError('You have already rated this user for the selected game.')

        # Only actual participants/host of the same game can rate each other.
        involved_user_ids = set(game.participants.exclude(status=ParticipantStatus.REMOVED).values_list('user_id', flat=True))
        involved_user_ids.add(game.host_id)
        if request.user.id not in involved_user_ids or int(to_user) not in involved_user_ids:
            raise serializers.ValidationError('Both users must be involved in the game.')
        attrs['to_user_id'] = int(to_user)
        return attrs

    def create(self, validated_data):
        to_user_id = validated_data.pop('to_user_id')
        rating = Rating.objects.create(from_user=self.context['request'].user, to_user_id=to_user_id, **validated_data)
        RatingService.refresh_profile_aggregates(rating.to_user)
        return rating
