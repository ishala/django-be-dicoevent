from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import Http404
from .serializers import EventSerializer, EventPosterSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.authentication import JWTAuthentication
from core.permissions import IsOwnerOrAdminOrSuperUser
from django.shortcuts import get_object_or_404
from django.core.cache import cache
import tempfile
import json
import os
import uuid
from minio import Minio
from .models import Event
from dico_event.logging_config import logger

def get_minio_client():
    return Minio(
        endpoint=os.getenv('MINIO_ENDPOINT_URL'),
        access_key=os.getenv('MINIO_ACCESS_KEY'),
        secret_key=os.getenv('MINIO_SECRET_KEY'),
        secure=False
    )

bucket_name = os.getenv('MINIO_BUCKET_NAME')

CACHE_KEY_LIST = "event_list"
CACHE_KEY_DETAIL = "event_detail_{}"

class EventListCreateView(APIView):
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return [IsAuthenticated()]

    def get(self, request):
        events = cache.get(CACHE_KEY_LIST)
        if not events:
            logger.info("Event list retrieved from database")
            events = Event.objects.all().order_by('name')[:10]
            cache.get(CACHE_KEY_LIST)
            serializer = EventSerializer(events, many=True)

            events_data = json.dumps(serializer.data, default=str)
            cache.set(CACHE_KEY_LIST, events_data, timeout=3600)
            events = events_data
            data_source = 'database'
        else:
            logger.info("Event list retrieved from cache")
            data_source = 'cache'

        response = Response({"events": json.loads(events)})
        response['X-Data-Source'] = data_source
        return response

    def post(self, request):
        serializer = EventSerializer(data=request.data)
        if serializer.is_valid():
            if not request.user.is_superuser and not request.user.groups.filter(name__in=['admin', 'organizer']).exists():
                logger.warning(f"Unauthorized event creation attempt by user {request.user}")
                return Response(
                    {"error": "You don't have permission to create an event."},
                    status=status.HTTP_403_FORBIDDEN
                )
            event = serializer.save()
            cache.delete(CACHE_KEY_LIST)
            logger.info(f"Event {event.id} created by {request.user}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.error(f"Event creation failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EventDetailView(APIView):
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        elif self.request.method in ["PUT", "DELETE"]:
            return [IsAuthenticated(), IsOwnerOrAdminOrSuperUser()]
        return [IsAuthenticated()]

    def get_object(self, pk):
        try:
            return Event.objects.get(pk=pk)
        except Event.DoesNotExist:
            logger.error(f"Event with id {pk} not found")
            raise Http404

    def get(self, request, pk):
        cache_key = CACHE_KEY_DETAIL.format(pk)
        event_data = cache.get(cache_key)

        if not event_data:
            logger.info(f"Event {pk} retrieved from database")
            event = self.get_object(pk)
            serializer = EventSerializer(event)
            
            event_data = json.dumps(serializer.data, default=str)
            cache.set(cache_key, event_data, timeout=3600)
            data_source = 'database'
        else:
            logger.info(f"Event {pk} retrieved from cache")
            data_source = 'cache'

        response = Response(json.loads(event_data))
        response['X-Data-Source'] = data_source
        return response

    def put(self, request, pk):
        event = self.get_object(pk)
        self.check_object_permissions(request, event) 
        serializer = EventSerializer(event, data=request.data, partial=True)

        if serializer.is_valid():
            event = serializer.save()
            cache.set(
                CACHE_KEY_DETAIL.format(pk),
                json.dumps(serializer.data, default=str),
                timeout=3600
            )
            logger.info(f"Event {event.id} updated by {request.user}")
            return Response(serializer.data)

        logger.error(f"Failed to update event {pk}: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        event = self.get_object(pk)
        self.check_object_permissions(request, event)
        event.delete()
        cache.delete(CACHE_KEY_DETAIL.format(pk))
        logger.info(f"Event {pk} deleted by {request.user}")
        return Response(status=status.HTTP_204_NO_CONTENT)


class EventPosterView(APIView):
    authentication_classes = [JWTAuthentication]
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        return [IsAuthenticated(), IsOwnerOrAdminOrSuperUser()]

    def post(self, request):
        serializer = EventPosterSerializer(data=request.data)
        if serializer.is_valid():
            file = request.data.get('image')
            if not file:
                logger.warning("Poster upload failed: No image provided")
                return Response({"message": "Image is required"}, status=status.HTTP_400_BAD_REQUEST)

            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                for chunk in file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name

            try:
                object_name = f"event_posters/{uuid.uuid4()}_{file.name}"
                client = get_minio_client()
                if not bucket_name:
                    logger.error("Poster upload failed: Minio bucket not configured")
                    return Response({"error": "Bucket not configured"}, status=500)
                client.fput_object(bucket_name, object_name, temp_file_path, content_type=file.content_type)

                poster = serializer.save(image=object_name)
                logger.info(f"Poster {poster.id} uploaded by {request.user}")
            except Exception as e:
                logger.exception(f"Upload to Minio failed: {str(e)}")
                return Response({"error": f"Upload to Minio failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            finally:
                os.remove(temp_file_path)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.error(f"Poster upload validation failed: {serializer.errors}")
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
        
        logger.info(f"Retrieved {len(images)} poster(s) for event {pk} by {request.user}")
        return Response(serialized_images)