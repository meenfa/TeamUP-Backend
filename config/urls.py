from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.auth_urls')),
    path('api/', include('accounts.profile_urls')),
    path('api/', include('games.urls')),
    path('api/', include('ratings.urls')),
    path('api/', include('notifications.urls')),
]
