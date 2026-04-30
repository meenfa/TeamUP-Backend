from django.urls import path

from .views import GoogleAuthView, LogoutView, TeamUpTokenRefreshView

urlpatterns = [
    path('google/', GoogleAuthView.as_view(), name='google-auth'),
    path('token/refresh/', TeamUpTokenRefreshView.as_view(), name='token-refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
