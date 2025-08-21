from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Ticket
from .serializers import TicketSerializer
from core.permissions import IsAdminOrSuperUser
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.core.cache import cache
import json
from dico_event.logging_config import logger

CACHE_KEY_TICKET_DETAIL = "ticket_detail_{}"

class TicketListCreateView(APIView):
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        elif self.request.method == 'POST':
            return [IsAdminOrSuperUser()]
        return [IsAuthenticated()]
    
    def get(self, request):
        tickets = Ticket.objects.all()
        serializer = TicketSerializer(tickets, many=True, context={'request': request})
        logger.info(f"{len(tickets)} tickets retrieved by {request.user}")
        return Response({'tickets': serializer.data})

    def post(self, request):
        serializer = TicketSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            ticket = serializer.save()
            logger.info(f"Ticket {ticket.id} created by {request.user}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.error(f"Ticket creation failed by {request.user} - {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TicketDetailView(APIView):
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        elif self.request.method in ['PUT', 'DELETE']:
            return [IsAdminOrSuperUser()]
        return [IsAuthenticated()]

    def get_object(self, pk):
        return get_object_or_404(Ticket, pk=pk)

    def get(self, request, pk):
        cache_key = CACHE_KEY_TICKET_DETAIL.format(pk)
        ticket_data = cache.get(cache_key)

        if not ticket_data:
            logger.info(f"Ticket {pk} retrieved from database by {request.user}")
            ticket = self.get_object(pk)
            serializer = TicketSerializer(ticket, context={'request': request})
            ticket_data = json.dumps(serializer.data, default=str)
            cache.set(cache_key, ticket_data, timeout=3600)
            data_source = 'database'
        else:
            logger.info(f"Ticket {pk} retrieved from cache by {request.user}")
            data_source = 'cache'

        response = Response(json.loads(ticket_data))
        response['X-Data-Source'] = data_source
        return response

    def put(self, request, pk):
        ticket = self.get_object(pk)
        serializer = TicketSerializer(ticket, data=request.data, context={'request': request}, partial=True)
        if serializer.is_valid():
            ticket = serializer.save()
            cache.set(
                CACHE_KEY_TICKET_DETAIL.format(pk),
                json.dumps(serializer.data, default=str),
                timeout=3600
            )
            logger.info(f"Ticket {ticket.id} updated by {request.user}")
            return Response(serializer.data)
        logger.error(f"Ticket {pk} update failed by {request.user} - {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        ticket = self.get_object(pk)
        ticket.delete()
        cache.delete(CACHE_KEY_TICKET_DETAIL.format(pk))
        logger.info(f"Ticket {pk} deleted by {request.user}")
        return Response(status=status.HTTP_204_NO_CONTENT)
