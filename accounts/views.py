from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser

from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.shortcuts import get_object_or_404
from common.mixins import StandardResponseMixin

from .serializers import (
    GoogleAuthSerializer,
    LogoutSerializer,
    ProfileSerializer,
)
from .models import User

from rest_framework.response import Response

from rest_framework.response import Response

from rest_framework.response import Response

class GoogleAuthView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)

        data = {
            "success": True,
            "message": "Google login successful",
            "data": {
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.full_name,
                    "username": user.username,
                }
            }
        }

        response = Response(data)

        # 🔥 DEBUG (MUST SEE IN TERMINAL)
        print("🔥 SETTING ACCESS COOKIE")

        response.set_cookie(
            "access",
            access,
            httponly=True,
            samesite="Lax",
            secure=False,
            path="/",
        )

        response.set_cookie(
            "refresh",
            str(refresh),
            httponly=True,
            samesite="Lax",
            secure=False,
            path="/",
        )

        print("🔥 COOKIE ADDED")

        return response
    
# Logout View
class LogoutView(StandardResponseMixin, APIView):
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        response = self.success_response(message="Logout successful.")

        response.delete_cookie("access")
        response.delete_cookie("refresh")

        return response


# Profile View
class ProfileView(StandardResponseMixin, generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_object(self):
        user = self.request.user
        print("USER:", user)

        if not user or user.is_anonymous:
            raise Exception("Not logged in")

        return user.profile

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return self.success_response(serializer.data)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.success_response(serializer.data, 'Profile updated successfully.')
    
# class [public profile view]
class PublicProfileView(StandardResponseMixin, APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, username):
        user = get_object_or_404(User, username=username)

        return self.success_response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "profile_photo": user.profile.profile_photo if hasattr(user, "profile") else None
        })

class TeamUpTokenRefreshView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]
