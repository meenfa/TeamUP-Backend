from django.urls import path

from .views import MyRatingsView, RatingCreateView

urlpatterns = [
    path('ratings/', RatingCreateView.as_view(), name='ratings-create'),
    path('ratings/me/', MyRatingsView.as_view(), name='ratings-me'),
]
