import base64
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User


class GoogleAuthFlowTests(APITestCase):
    @patch('accounts.services.GoogleAuthService._verify_id_token')
    def test_google_auth_creates_verified_user_and_returns_tokens(self, mock_verify):
        mock_verify.return_value = {
            'sub': 'google-user-1',
            'email': 'googleuser@example.com',
            'email_verified': True,
            'name': 'Google User',
        }

        response = self.client.post(
            reverse('google-auth'),
            {'credential': 'google-id-token'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = User.objects.get(email='googleuser@example.com')
        self.assertEqual(user.google_sub, 'google-user-1')
        self.assertTrue(user.is_verified)
        self.assertTrue(hasattr(user, 'profile'))
        self.assertIn('access', response.data['data'])
        self.assertIn('refresh', response.data['data'])

    @patch('accounts.services.GoogleAuthService._verify_id_token')
    def test_google_auth_links_existing_user_by_email(self, mock_verify):
        user = User.objects.create_user(
            email='googleuser@example.com',
            password='password123',
            full_name='Existing User',
        )
        mock_verify.return_value = {
            'sub': 'google-user-2',
            'email': 'googleuser@example.com',
            'email_verified': True,
            'name': 'Existing User Updated',
        }

        response = self.client.post(
            reverse('google-auth'),
            {'id_token': 'google-id-token'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.google_sub, 'google-user-2')
        self.assertTrue(user.is_verified)
        self.assertEqual(user.full_name, 'Existing User Updated')

    @patch('accounts.services.GoogleAuthService._verify_id_token')
    def test_google_auth_tokens_can_refresh(self, mock_verify):
        mock_verify.return_value = {
            'sub': 'google-user-3',
            'email': 'refreshuser@example.com',
            'email_verified': True,
            'name': 'Refresh User',
        }

        auth_response = self.client.post(
            reverse('google-auth'),
            {'credential': 'google-id-token'},
            format='json',
        )

        refresh_response = self.client.post(
            reverse('token-refresh'),
            {'refresh': auth_response.data['data']['refresh']},
            format='json',
        )

        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_response.data)


class ProfileFlowTests(APITestCase):
    tiny_gif = base64.b64decode('R0lGODdhAQABAIABAP///wAAACwAAAAAAQABAAACAkQBADs=')

    def setUp(self):
        self.user = User.objects.create_user(
            email='player@example.com',
            password=None,
            full_name='Player One',
            google_sub='google-player-1',
            is_verified=True,
        )

    @patch('accounts.services.GoogleAuthService._verify_id_token')
    def test_profile_retrieve_and_update_after_google_sign_in(self, mock_verify):
        mock_verify.return_value = {
            'sub': 'google-player-1',
            'email': 'player@example.com',
            'email_verified': True,
            'name': 'Player One',
        }

        auth_response = self.client.post(
            reverse('google-auth'),
            {'credential': 'google-id-token'},
            format='json',
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {auth_response.data['data']['access']}")

        retrieve_response = self.client.get(reverse('profile'))
        self.assertEqual(retrieve_response.status_code, status.HTTP_200_OK)
        self.assertEqual(retrieve_response.data['data']['email'], 'player@example.com')

        profile_photo = SimpleUploadedFile('avatar.gif', self.tiny_gif, content_type='image/gif')
        update_response = self.client.patch(
            reverse('profile'),
            {
                'full_name': 'Player One Updated',
                'phone_number': '9800000001',
                'city': 'Kathmandu',
                'preferred_area': 'Baneshwor',
                'bio': 'Weekend futsal player',
                'profile_photo': profile_photo,
            },
            format='multipart',
        )

        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, 'Player One Updated')
        self.assertEqual(self.user.phone_number, '9800000001')
        self.assertEqual(self.user.profile.city, 'Kathmandu')
        self.assertTrue(bool(self.user.profile.profile_photo))
