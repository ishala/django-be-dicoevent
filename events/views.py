from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import Http404
import tempfile
import os
import uuid
from minio import Minio
from .models import Event
from .serializers import EventSerializer, EventPosterSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.authentication import JWTAuthentication
from core.permissions import (
    IsOwnerOrAdminOrSuperUser,
)
from django.shortcuts import get_object_or_404

def get_minio_client():
    return Minio(
        endpoint=os.getenv('MINIO_ENDPOINT_URL'),
        access_key=os.getenv('MINIO_ACCESS_KEY'),
        secret_key=os.getenv('MINIO_SECRET_KEY'),
        secure=False
    )

bucket_name = os.getenv('MINIO_BUCKET_NAME')

class EventListCreateView(APIView):
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'POST':
            # Organizer, Admin, Superuser boleh create
            return [IsAuthenticated()]
        return [IsAuthenticated()]

    def get(self, request):
        events = Event.objects.all().order_by('name')[:10]
        serializer = EventSerializer(events, many=True)
        return Response({'events': serializer.data})

    def post(self, request):
        serializer = EventSerializer(data=request.data)
        if serializer.is_valid():
            if not request.user.is_superuser and not request.user.groups.filter(name__in=['admin', 'organizer']).exists():
                return Response(
                    {"error": "You don't have permission to create an event."},
                    status=status.HTTP_403_FORBIDDEN
                )
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EventDetailView(APIView):
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]  # semua orang bisa akses detail event
        elif self.request.method in ["PUT", "DELETE"]:
            return [IsAuthenticated(), IsOwnerOrAdminOrSuperUser()]
        return [IsAuthenticated()]

    def get_object(self, pk):
        try:
            return Event.objects.get(pk=pk)
        except Event.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        event = self.get_object(pk)
        serializer = EventSerializer(event)
        return Response(serializer.data)

    def put(self, request, pk):
        event = self.get_object(pk)
        self.check_object_permissions(request, event) 
        serializer = EventSerializer(event, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        event = self.get_object(pk)
        self.check_object_permissions(request, event)
        event.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class EventPosterView(APIView):
    authentication_classes = [JWTAuthentication]
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        # hanya Admin & Superuser boleh upload poster
        return [IsAuthenticated(), IsOwnerOrAdminOrSuperUser()]

    def post(self, request):
        serializer = EventPosterSerializer(data=request.data)
        if serializer.is_valid():
            file = request.data.get('image')
            if not file:
                return Response(
                    {"message": "Image is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                for chunk in file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name

            try:
                object_name = f"event_posters/{uuid.uuid4()}_{file.name}"
                client = get_minio_client()
                if not bucket_name:
                    return Response({"error": "Bucket not configured"}, status=500)
                client.fput_object(bucket_name, object_name, temp_file_path, content_type=file.content_type)

                serializer.save(image=object_name)
            except Exception as e:
                return Response(
                    {"error": f"Upload to Minio failed: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            finally:
                os.remove(temp_file_path)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EventPosterDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        images = event.eventposter_set.all()

        serialized_images = []
        for image in images:
            client = get_minio_client()
            presigned_url = client.presigned_get_object(
                bucket_name,
                image.image.name,
                response_headers={"response-content-type": "image/jpeg"}
            )
            serialized_images.append({"id": image.id, "url": presigned_url})
        
        return Response(serialized_images)