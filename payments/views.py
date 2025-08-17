from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import Http404
from .models import Payment, Registration
from .serializers import PaymentSerializer, RegistrationSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from core.permissions import IsAdminOrSuperUser

class PaymentListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        if IsAdminOrSuperUser().has_permission(request, self):
            payments = Payment.objects.all()
        else:
            payments = Payment.objects.filter(registration_id__user_id=request.user)
        serializer = PaymentSerializer(payments, many=True, context={'request': request})
        return Response({'payments': serializer.data})

    def post(self, request):
        serializer = PaymentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # Validasi: hanya boleh create payment untuk registrasi miliknya
            reg = serializer.validated_data['registration_id']
            if not IsAdminOrSuperUser().has_permission(request, self) and reg.user_id != request.user:
                return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PaymentDetailView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_object(self, pk):
        try:
            return Payment.objects.get(pk=pk)
        except Payment.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        payment = self.get_object(pk)
        if not IsAdminOrSuperUser().has_permission(request, self) and payment.registration_id.user_id != request.user:
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        serializer = PaymentSerializer(payment, context={'request': request})
        return Response(serializer.data)

    def put(self, request, pk):
        payment = self.get_object(pk)
        if not IsAdminOrSuperUser().has_permission(request, self):
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        serializer = PaymentSerializer(payment, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        payment = self.get_object(pk)
        if not IsAdminOrSuperUser(request.user):
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        payment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RegistrationListCreateView(APIView):
    authentication_classes = [JWTAuthentication]
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]  # Semua user bisa mendaftar
        elif self.request.method == 'GET':
            return [IsAdminOrSuperUser()]  # Admin/superuser melihat semua
        return [IsAuthenticated()]

    def get(self, request):
        if IsAdminOrSuperUser().has_permission(request, self):
            registrations = Registration.objects.all()
        else:
            registrations = Registration.objects.filter(user_id=request.user)
        serializer = RegistrationSerializer(registrations, many=True)
        return Response({'registrations': serializer.data})

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            # Validasi user hanya boleh mendaftarkan dirinya sendiri
            reg_user = serializer.validated_data['user_id']
            if not IsAdminOrSuperUser().has_permission(request, self) and reg_user != request.user:
                return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RegistrationDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]  # Semua user bisa lihat detail miliknya
        elif self.request.method in ['PUT', 'DELETE']:
            return [IsAdminOrSuperUser()]
        return [IsAuthenticated()]

    def get_object(self, pk):
        try:
            return Registration.objects.get(pk=pk)
        except Registration.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        reg = self.get_object(pk)
        if not IsAdminOrSuperUser().has_permission(request, self) and reg.user_id != request.user:
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        serializer = RegistrationSerializer(reg)
        return Response(serializer.data)

    def put(self, request, pk):
        if not IsAdminOrSuperUser().has_permission(request, self):
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        reg = self.get_object(pk)
        serializer = RegistrationSerializer(reg, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        if not IsAdminOrSuperUser().has_permission(request, self):
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        reg = self.get_object(pk)
        reg.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
