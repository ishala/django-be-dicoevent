from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import Http404
from .models import Payment, Registration
from .serializers import PaymentSerializer, RegistrationSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from core.permissions import IsAdminOrSuperUser
from django.core.cache import cache
import json
from .tasks import send_ticket_reminder_email
from dico_event.logging_config import logger

CACHE_KEY_PAYMENT_DETAIL = "payment_detail_{}"
CACHE_KEY_REGIST_DETAIL = "regist_detail_{}"


class PaymentListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        if IsAdminOrSuperUser().has_permission(request, self):
            payments = Payment.objects.all()
            logger.info(f"Admin {request.user} retrieved all payments")
        else:
            payments = Payment.objects.filter(registration_id__user_id=request.user)
            logger.info(f"User {request.user} retrieved own payments")
        serializer = PaymentSerializer(payments, many=True, context={'request': request})
        return Response({'payments': serializer.data})

    def post(self, request):
        serializer = PaymentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            reg = serializer.validated_data['registration_id']
            if not IsAdminOrSuperUser().has_permission(request, self) and reg.user_id != request.user:
                logger.warning(f"User {request.user} tried to create payment for another user’s registration {reg.id}")
                return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
            
            payment = serializer.save()
            logger.info(f"Payment {payment.id} created by {request.user}")
            return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)
        logger.error(f"Payment creation failed by {request.user}: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PaymentDetailView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_object(self, pk):
        try:
            return Payment.objects.get(pk=pk)
        except Payment.DoesNotExist:
            logger.error(f"Payment {pk} not found")
            raise Http404

    def get(self, request, pk):
        cache_key = CACHE_KEY_PAYMENT_DETAIL.format(pk)
        payment_data = cache.get(cache_key)

        if not payment_data:
            logger.info(f"Payment {pk} retrieved from database")
            payment = self.get_object(pk)
            if not IsAdminOrSuperUser().has_permission(request, self) and payment.registration_id.user_id != request.user:
                logger.warning(f"User {request.user} tried to access payment {pk} not owned")
                return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

            serializer = PaymentSerializer(payment, context={'request': request})
            payment_data = dict(serializer.data)
            cache.set(cache_key, json.dumps(payment_data, default=str), timeout=3600)
            data_source = 'database'
        else:
            logger.info(f"Payment {pk} retrieved from cache")
            payment_data = json.loads(payment_data)
            data_source = 'cache'
        
        response = Response(payment_data)
        response['X-Data-Source'] = data_source
        return response

    def put(self, request, pk):
        payment = self.get_object(pk)
        if not IsAdminOrSuperUser().has_permission(request, self):
            logger.warning(f"User {request.user} tried to update payment {pk} without permission")
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        serializer = PaymentSerializer(payment, data=request.data, context={'request': request}, partial=True)
        if serializer.is_valid():
            payment = serializer.save()
            cache.set(
                CACHE_KEY_PAYMENT_DETAIL.format(pk),
                json.dumps(dict(PaymentSerializer(payment).data), default=str),
                timeout=3600
            )
            logger.info(f"Payment {pk} updated by {request.user}")
            return Response(PaymentSerializer(payment).data)
        logger.error(f"Payment update failed for {pk} by {request.user}: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        payment = self.get_object(pk)
        if not IsAdminOrSuperUser().has_permission(request, self):
            logger.warning(f"User {request.user} tried to delete payment {pk} without permission")
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        payment.delete()
        cache.delete(CACHE_KEY_PAYMENT_DETAIL.format(pk))
        logger.info(f"Payment {pk} deleted by {request.user}")
        return Response(status=status.HTTP_204_NO_CONTENT)


class RegistrationListCreateView(APIView):
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        elif self.request.method == 'GET':
            return [IsAdminOrSuperUser()]
        return [IsAuthenticated()]

    def get(self, request):
        if IsAdminOrSuperUser().has_permission(request, self):
            registrations = Registration.objects.all()
            logger.info(f"Admin {request.user} retrieved all registrations")
        else:
            registrations = Registration.objects.filter(user_id=request.user)
            logger.info(f"User {request.user} retrieved own registrations")
        serializer = RegistrationSerializer(registrations, many=True)
        return Response({'registrations': serializer.data})

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            reg_user = serializer.validated_data['user_id']
            if not IsAdminOrSuperUser().has_permission(request, self) and reg_user != request.user:
                logger.warning(f"User {request.user} tried to register for another user {reg_user}")
                return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
            
            registration = serializer.save()
            logger.info(f"Registration {registration.id} created by {request.user}")

            # kirim email reminder
            send_ticket_reminder_email(
                registration.user_id.email,
                registration.user_id.username,
                registration.ticket_id.event_id.name
            )
            logger.info(f"Reminder email sent to {registration.user_id.email} for registration {registration.id}")
            return Response(RegistrationSerializer(registration).data, status=status.HTTP_201_CREATED)
        logger.error(f"Registration creation failed by {request.user}: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RegistrationDetailView(APIView):
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        elif self.request.method in ['PUT', 'DELETE']:
            return [IsAdminOrSuperUser()]
        return [IsAuthenticated()]

    def get_object(self, pk):
        try:
            return Registration.objects.get(pk=pk)
        except Registration.DoesNotExist:
            logger.error(f"Registration {pk} not found")
            raise Http404

    def get(self, request, pk):
        cache_key = CACHE_KEY_REGIST_DETAIL.format(pk)
        regist_data = cache.get(cache_key)

        if not regist_data:
            logger.info(f"Registration {pk} retrieved from database")
            regist = self.get_object(pk)
            if not IsAdminOrSuperUser().has_permission(request, self) and regist.user_id != request.user:
                logger.warning(f"User {request.user} tried to access registration {pk} not owned")
                return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

            serializer = RegistrationSerializer(regist)
            regist_data = dict(serializer.data)
            cache.set(cache_key, json.dumps(regist_data, default=str), timeout=3600)
            data_source = 'database'
        else:
            logger.info(f"Registration {pk} retrieved from cache")
            regist_data = json.loads(regist_data)
            data_source = 'cache'

        response = Response(regist_data)
        response['X-Data-Source'] = data_source
        return response

    def put(self, request, pk):
        if not IsAdminOrSuperUser().has_permission(request, self):
            logger.warning(f"User {request.user} tried to update registration {pk} without permission")
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        reg = self.get_object(pk)
        serializer = RegistrationSerializer(reg, data=request.data, partial=True)
        if serializer.is_valid():
            reg = serializer.save()
            cache.set(
                CACHE_KEY_REGIST_DETAIL.format(pk),
                json.dumps(dict(RegistrationSerializer(reg).data), default=str),
                timeout=3600
            )
            logger.info(f"Registration {pk} updated by {request.user}")
            return Response(RegistrationSerializer(reg).data)
        logger.error(f"Registration update failed for {pk} by {request.user}: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        if not IsAdminOrSuperUser().has_permission(request, self):
            logger.warning(f"User {request.user} tried to delete registration {pk} without permission")
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        reg = self.get_object(pk)
        reg.delete()
        cache.delete(CACHE_KEY_REGIST_DETAIL.format(pk))
        logger.info(f"Registration {pk} deleted by {request.user}")
        return Response(status=status.HTTP_204_NO_CONTENT)
