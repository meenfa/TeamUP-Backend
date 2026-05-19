from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response

from common.mixins import StandardResponseMixin

from .filters import GameFilter
from .models import Game
from .permissions import IsHostOrReadOnly
from .serializers import GameSerializer, MarkParticipantStatusSerializer, ParticipantDecisionSerializer
from .services import GameService


class GameViewSet(StandardResponseMixin, viewsets.ModelViewSet):
    queryset = Game.objects.select_related('host', 'host__profile').prefetch_related('participants__user__profile').all()
    serializer_class = GameSerializer
    permission_classes = [permissions.IsAuthenticated, IsHostOrReadOnly]
    filterset_class = GameFilter
    search_fields = ['location_name', 'area_city', 'description']
    ordering_fields = ['game_date', 'start_time', 'created_at']

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        # return Response({'success': True, 'message': 'Games fetched successfully.', 'data': response.data}, status=response.status_code)
        return self.success_response(response.data, 'Games fetched successfully.')
    
    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return self.success_response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        game = serializer.save()
        return self.success_response(self.get_serializer(game).data, 'Game created successfully.', status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.success_response(
            self.get_serializer(instance).data,
            'Game updated successfully.'
        )
    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        game = self.get_object()
        participant = GameService.join_game(game, request.user)
        return self.success_response({'participant_id': participant.id, 'status': participant.status}, 'Join request submitted successfully.', status.HTTP_201_CREATED)

    # detail = true means this action works on a SINGLE object using its ID (pk)
    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        game = self.get_object()
        participant = GameService.leave_game(game, request.user)
        return self.success_response({'participant_id': participant.id, 'status': participant.status}, 'Left game successfully.')

    @action(detail=True, methods=['post'], url_path='confirm-attendance')
    def confirm_attendance(self, request, pk=None):
        game = self.get_object()
        participant = GameService.confirm_attendance(game, request.user)
        return self.success_response({'participant_id': participant.id, 'status': participant.status}, 'Attendance confirmed successfully.')

    @action(detail=True, methods=['post'], url_path='approve-participant')
    def approve_participant(self, request, pk=None):
        game = self.get_object()
        serializer = ParticipantDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        participant = GameService.approve_participant(game, request.user, serializer.validated_data['participant_user_id'])
        return self.success_response({'participant_id': participant.id, 'status': participant.status}, 'Participant approved successfully.')

    @action(detail=True, methods=['post'], url_path='reject-participant')
    def reject_participant(self, request, pk=None):
        game = self.get_object()
        serializer = ParticipantDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        participant = GameService.reject_participant(game, request.user, serializer.validated_data['participant_user_id'])
        return self.success_response({'participant_id': participant.id, 'status': participant.status}, 'Participant rejected successfully.')

    @action(detail=True, methods=['post'], url_path='mark-participant-status')
    def mark_participant_status(self, request, pk=None):
        game = self.get_object()
        serializer = MarkParticipantStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        participant = GameService.mark_participant_status(
            game,
            request.user,
            serializer.validated_data['participant_user_id'],
            serializer.validated_data['status'],
        )
        return self.success_response({'participant_id': participant.id, 'status': participant.status}, 'Participant status updated.')


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_games(request):
    payload = {key: GameSerializer(queryset, many=True, context={'request': request}).data for key, queryset in GameService.my_games_queryset(request.user).items()}
    return Response({'success': True, 'message': 'My games fetched successfully.', 'data': payload})
