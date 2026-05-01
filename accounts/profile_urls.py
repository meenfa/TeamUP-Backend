from django.urls import path

from .views import ProfileView,PublicProfileView

urlpatterns = [
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/<str:username>/', PublicProfileView.as_view(), name='public-profile'),
]
