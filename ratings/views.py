from rest_framework import generics, status
from rest_framework.response import Response

from .models import Rating
from .serializers import RatingSerializer


class RatingCreateView(generics.CreateAPIView):
    serializer_class = RatingSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rating = serializer.save()
        return Response({'success': True, 'message': 'Rating submitted successfully.', 'data': RatingSerializer(rating, context={'request': request}).data}, status=status.HTTP_201_CREATED)


class MyRatingsView(generics.ListAPIView):
    serializer_class = RatingSerializer

    def get_queryset(self):
        return Rating.objects.filter(to_user=self.request.user).select_related('from_user', 'to_user', 'game')

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({'success': True, 'message': 'Ratings fetched successfully.', 'data': response.data}, status=response.status_code)
