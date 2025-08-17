from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import Http404
from .models import Ticket
from .serializers import TicketSerializer
from core.permissions import IsAdminOrSuperUser
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

# Create your views here.
class TicketListCreateView(APIView):
    authentication_classes = [JWTAuthentication]
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]  # Semua user bisa GET
        elif self.request.method == 'POST':
            return [IsAdminOrSuperUser()]  # Hanya admin/superuser bisa POST
        return [IsAuthenticated()]
    
    def get(self, request):
        tickets = Ticket.objects.all()
        serializer = TicketSerializer(tickets, many=True, context={'request': request})
        return Response({'tickets': serializer.data})

    def post(self, request):
        serializer = TicketSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TicketDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]  # Semua user bisa GET detail
        elif self.request.method in ['PUT', 'DELETE']:
            return [IsAdminOrSuperUser()]  # Hanya admin/superuser
        return [IsAuthenticated()]

    def get_object(self, pk):
        try:
            return Ticket.objects.get(pk=pk)
        except Ticket.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        ticket = self.get_object(pk=pk)
        serializer = TicketSerializer(ticket, context={'request': request})
        return Response(serializer.data)

    def put(self, request, pk):
        ticket = self.get_object(pk=pk)
        serializer = TicketSerializer(ticket, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        ticket = self.get_object(pk=pk)
        ticket.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    