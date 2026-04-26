from datetime import date, timedelta, time

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from games.models import Game, GameParticipant


class GamePermissionTests(APITestCase):
    def setUp(self):
        self.host = User.objects.create_user(
            email='host@example.com',
            password='password123',
            full_name='Host User',
            is_verified=True,
        )
        self.player = User.objects.create_user(
            email='player@example.com',
            password='password123',
            full_name='Player User',
            is_verified=True,
        )
        self.game = Game.objects.create(
            host=self.host,
            location_name='TeamUp Arena',
            area_city='Kathmandu',
            game_date=date.today() + timedelta(days=1),
            start_time=time(18, 0),
            end_time=time(19, 30),
            total_players=10,
            skill_level='mixed',
            entry_fee='200.00',
            payment_note='Pay on arrival',
            description='Friendly evening futsal',
        )

    def test_non_host_can_join_game(self):
        self.client.force_authenticate(user=self.player)

        response = self.client.post(reverse('games-join', args=[self.game.id]))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        participant = GameParticipant.objects.get(game=self.game, user=self.player)
        self.assertEqual(participant.status, 'pending')

    def test_non_host_cannot_patch_game(self):
        self.client.force_authenticate(user=self.player)

        response = self.client.patch(
            reverse('games-detail', args=[self.game.id]),
            {'description': 'Trying to edit someone else game'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_host_can_approve_pending_participant(self):
        GameParticipant.objects.create(game=self.game, user=self.player, status='pending')
        self.client.force_authenticate(user=self.host)

        response = self.client.post(
            reverse('games-approve-participant', args=[self.game.id]),
            {'participant_user_id': self.player.id},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        participant = GameParticipant.objects.get(game=self.game, user=self.player)
        self.assertEqual(participant.status, 'confirmed')

    def test_pending_participant_cannot_confirm_attendance(self):
        GameParticipant.objects.create(game=self.game, user=self.player, status='pending')
        self.client.force_authenticate(user=self.player)

        response = self.client.post(reverse('games-confirm-attendance', args=[self.game.id]))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
