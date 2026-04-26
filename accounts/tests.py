from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User
from .verification import build_email_verification_token


class EmailVerificationFlowTests(APITestCase):
    registration_payload = {
        'email': 'user1@example.com',
        'phone_number': '9800000001',
        'full_name': 'User One',
        'password': 'password123',
    }

    @patch('accounts.services.safe_dispatch')
    def test_register_sends_verification_email_and_leaves_user_unverified(self, mock_dispatch):
        response = self.client.post(reverse('register'), self.registration_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email=self.registration_payload['email'])
        self.assertFalse(user.is_verified)
        self.assertIsNotNone(user.verification_email_sent_at)
        mock_dispatch.assert_called_once()

    def test_unverified_user_cannot_login(self):
        User.objects.create_user(
            email='user1@example.com',
            password='password123',
            full_name='User One',
        )

        response = self.client.post(
            reverse('login'),
            {'email': 'user1@example.com', 'password': 'password123'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Account is not verified.', str(response.data))

    def test_verify_email_marks_user_verified(self):
        user = User.objects.create_user(
            email='user1@example.com',
            password='password123',
            full_name='User One',
        )
        token = build_email_verification_token(user)

        response = self.client.get(reverse('verify-email'), {'token': token})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.is_verified)

    @patch('accounts.services.safe_dispatch')
    def test_resend_verification_resends_for_unverified_user(self, mock_dispatch):
        User.objects.create_user(
            email='user1@example.com',
            password='password123',
            full_name='User One',
        )

        response = self.client.post(
            reverse('resend-verification'),
            {'email': 'user1@example.com'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_dispatch.assert_called_once()
