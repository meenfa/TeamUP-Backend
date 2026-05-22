import pytest

@pytest.fixture
def user(db):
    """Create a test user for ANY test in ANY app"""
    from accounts.tests.factories import UserFactory
    return UserFactory()

@pytest.fixture
def api_client():
    """Create API client for testing endpoints"""
    from rest_framework.test import APIClient
    return APIClient()

@pytest.fixture
def auth_client(user, api_client):
    """Create authenticated client (handy for testing protected endpoints)"""
    api_client.force_authenticate(user=user)
    return api_client