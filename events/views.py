from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import Http404
from .models import Event
from .serializers import EventSerializer
from rest_framework.permissions import IsAuthenticated

# Create your views here.
class EventListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        event = Event.objects.all().order_by('name')[:10]
        serializer = EventSerializer(event, many=True)
        return Response({'events': serializer.data})

    def post(self, request):
        self.check_permissions(request)
        serializer = EventSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EventDetailView(APIView):
    # permission_classes = [IsOrganizerOrAdminOrSuperUser]

    def get_object(self, pk):
        try:
            event = Event.objects.get(pk=pk)
            self.check_object_permissions(self.request, event)
            return event
        except Event.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        event = self.get_object(pk=pk)
        serializer = EventSerializer(event)
        return Response(serializer.data)

    def put(self, request, pk):
        event = self.get_object(pk=pk)
        serializer = EventSerializer(event, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        event = self.get_object(pk=pk)
        event.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)