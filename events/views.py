from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import Http404
import tempfile
import os
from minio import Minio
from .models import Event
from .serializers import EventSerializer, EventPosterSerializer
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.authentication import JWTAuthentication

def get_minio_client():
    return Minio(
        endpoint=os.getenv('MINIO_ENDPOINT_URL'),
        access_key=os.getenv('MINIO_ACCESS_KEY'),
        secret_key=os.getenv('MINIO_SECRET_KEY'),
        secure=False
    )

bucket_name = os.getenv('MINIO_BUCKET_NAME')

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

class EventPosterView(APIView):
    authentication_classes = [JWTAuthentication]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_permissions(self):
        return [IsAuthenticated(), IsAdminUser()]

    def post(self, request):
        serializer = EventPosterSerializer(data=request.data)
        file = request.data.get('image')

        if serializer.is_valid():
            serializer.save()
            
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                for chunk in file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name

            try:
                object_name = f"{serializer.instance.image.name}"
                client = get_minio_client()
                client.fput_object(bucket_name, object_name, temp_file_path, content_type=file.content_type)
            except Exception as e:
                return Response(
                    {"error": f"Upload to Minio failed: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            finally:
                os.remove(temp_file_path)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)