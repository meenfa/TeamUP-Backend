from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import GameViewSet, my_games

router = DefaultRouter()
router.register('games', GameViewSet, basename='games')

urlpatterns = [
    path('', include(router.urls)),
    path('my-games/', my_games, name='my-games'),
]
