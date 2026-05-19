from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from accounts.services import ReliabilityService
from notifications.models import Notification
from notifications.tasks import schedule_game_reminder_task
from notifications.utils import safe_dispatch

from common.constants import GameStatus, NotificationType, ParticipantStatus

from .models import Game, GameParticipant


class GameService:
    @staticmethod
    @transaction.atomic
    def join_game(game: Game, user):
        profile = ReliabilityService.clear_expired_restriction_if_needed(user.profile)
        if profile.is_temporarily_restricted:
            raise ValueError('You are temporarily restricted from joining games.')
        if game.host_id == user.id:
            raise ValueError('Host is already part of the game as organizer.')
        if game.status in [GameStatus.CANCELLED, GameStatus.COMPLETED]:
            raise ValueError('Cannot join this game.')
        if game.available_slots <= 0:
            game.refresh_status()
            raise ValueError('Game is already full.')

        participant, created = GameParticipant.objects.select_for_update().get_or_create(
            game=game,
            user=user,
            defaults={'status': ParticipantStatus.PENDING},
        )
        if not created and participant.status not in [ParticipantStatus.CANCELLED, ParticipantStatus.REMOVED]:
            raise ValueError('You have already joined this game.')
        if not created:
            participant.status = ParticipantStatus.PENDING
            participant.removed_by_host = False
            participant.save(update_fields=['status', 'removed_by_host'])

        # Existing notification to the user who joined
        Notification.objects.create(
            user=user,
            notification_type=NotificationType.JOIN_CONFIRMATION,
            title='Join request submitted',
            message=f'Your request to join the game at {game.location_name} on {game.game_date} is pending host approval.',
        )
        
        # notify the host abt new join request
        Notification.objects.create(
            user=user,
            notification_type=NotificationType.JOIN_REQUEST,
            title='New Join request',
             message=f'{user.full_name} wants to join your game "{game.title}" on {game.game_date}',
       )
        
        return participant

    @staticmethod
    @transaction.atomic
    def approve_participant(game: Game, host_user, participant_user_id: int):
        if game.host_id != host_user.id:
            raise PermissionError('Only the host can approve join requests.')
        participant = GameParticipant.objects.select_for_update().filter(game=game, user_id=participant_user_id).first()
        if not participant:
            raise ValueError('Participant not found in this game.')
        if participant.status != ParticipantStatus.PENDING:
            raise ValueError('Only pending join requests can be approved.')
        if game.available_slots <= 0:
            game.refresh_status()
            raise ValueError('Game is already full.')

        participant.status = ParticipantStatus.CONFIRMED
        participant.removed_by_host = False
        participant.save(update_fields=['status', 'removed_by_host'])
        game.refresh_status()
        Notification.objects.create(
            user=participant.user,
            notification_type=NotificationType.JOIN_CONFIRMATION,
            title='Join request approved',
            message=f'Your request for the game at {game.location_name} on {game.game_date} was approved.',
        )
        safe_dispatch(schedule_game_reminder_task, game.id, participant.user_id)
        return participant

    @staticmethod
    @transaction.atomic
    def reject_participant(game: Game, host_user, participant_user_id: int):
        if game.host_id != host_user.id:
            raise PermissionError('Only the host can reject join requests.')
        participant = GameParticipant.objects.select_for_update().filter(game=game, user_id=participant_user_id).first()
        if not participant:
            raise ValueError('Participant not found in this game.')
        if participant.status != ParticipantStatus.PENDING:
            raise ValueError('Only pending join requests can be rejected.')

        participant.status = ParticipantStatus.REMOVED
        participant.removed_by_host = True
        participant.save(update_fields=['status', 'removed_by_host'])
        game.refresh_status()
        Notification.objects.create(
            user=participant.user,
            notification_type=NotificationType.SYSTEM,
            title='Join request rejected',
            message=f'Your request for the game at {game.location_name} on {game.game_date} was rejected by the host.',
        )
        return participant

    @staticmethod
    @transaction.atomic
    def leave_game(game: Game, user):
        participant = GameParticipant.objects.select_for_update().filter(game=game, user=user).first()
        if not participant or participant.status in [ParticipantStatus.CANCELLED, ParticipantStatus.REMOVED]:
            raise ValueError('You are not an active participant in this game.')
        participant.status = ParticipantStatus.CANCELLED
        participant.save(update_fields=['status'])
        game.refresh_status()
        return participant

    @staticmethod
    @transaction.atomic
    def confirm_attendance(game: Game, user):
        participant = GameParticipant.objects.select_for_update().filter(game=game, user=user).first()
        if not participant:
            raise ValueError('You have not joined this game.')
        if participant.status == ParticipantStatus.PENDING:
            raise ValueError('Your join request is still pending host approval.')
        if participant.status in [ParticipantStatus.REMOVED, ParticipantStatus.CANCELLED]:
            raise ValueError('Inactive participant cannot confirm attendance.')
        participant.status = ParticipantStatus.CONFIRMED
        participant.attendance_confirmed_at = timezone.now()
        participant.save(update_fields=['status', 'attendance_confirmed_at'])
        return participant

    @staticmethod
    @transaction.atomic
    def mark_participant_status(game: Game, host_user, participant_user_id: int, status: str):
        if game.host_id != host_user.id:
            raise PermissionError('Only the host can mark participant status.')
        participant = GameParticipant.objects.select_for_update().filter(game=game, user_id=participant_user_id).first()
        if not participant:
            raise ValueError('Participant not found in this game.')
        if status not in [ParticipantStatus.ATTENDED, ParticipantStatus.NO_SHOW, ParticipantStatus.REMOVED]:
            raise ValueError('Invalid status transition.')

        participant.status = status
        participant.removed_by_host = status == ParticipantStatus.REMOVED
        participant.save(update_fields=['status', 'removed_by_host'])

        if status in [ParticipantStatus.ATTENDED, ParticipantStatus.NO_SHOW]:
            ReliabilityService.apply_attendance_result(participant.user, attended=status == ParticipantStatus.ATTENDED)
        if status == ParticipantStatus.REMOVED:
            game.refresh_status()
        return participant

    @staticmethod
    def my_games_queryset(user):
        now = timezone.now().date()
        return {
            'hosted': Game.objects.filter(host=user),
            'joined': Game.objects.filter(participants__user=user).distinct(),
            'upcoming': Game.objects.filter(Q(host=user) | Q(participants__user=user), game_date__gte=now).distinct(),
            'past': Game.objects.filter(Q(host=user) | Q(participants__user=user), game_date__lt=now).distinct(),
        }
