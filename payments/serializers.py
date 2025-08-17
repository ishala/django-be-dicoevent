from rest_framework import serializers
from rest_framework.reverse import reverse
from .models import Payment, Registration
from core.models import User

class RegistrationSerializer(serializers.ModelSerializer):
    _links = serializers.SerializerMethodField()
    ticket = serializers.CharField(source='ticket_id.name', read_only=True)
    user = serializers.CharField(source='user_id.username', read_only=True)

    class Meta:
        model = Registration
        fields = ['id', 'ticket_id', 'user_id', 'ticket', 'user', '_links']

    def get__links(self, obj):
        request = self.context.get('request')
        return [
            {
                "rel": "self",
                "href": reverse('registration-list', request=request),
                "action": "POST",
                "types": ["application/json"]
            },
            {
                "rel": "self",
                "href": reverse('registration-detail', kwargs={'pk': obj.pk}, request=request),
                "action": "GET",
                "types": ["application/json"]
            },
            {
                "rel": "self",
                "href": reverse('registration-detail', kwargs={'pk': obj.pk}, request=request),
                "action": "PUT",
                "types": ["application/json"]
            },
            {
                "rel": "self",
                "href": reverse('registration-detail', kwargs={'pk': obj.pk}, request=request),
                "action": "DELETE",
                "types": ["application/json"]
            },
        ]

class PaymentSerializer(serializers.ModelSerializer):
    _links = serializers.SerializerMethodField()
    registration = serializers.CharField(source='registration_id.id', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'registration_id', 'payment_method',
            'payment_status', 'amount_paid', 'registration', '_links'
        ]

    def get__links(self, obj):
        request = self.context.get('request')
        return [
            {
                "rel": "self",
                "href": reverse('payment-list', request=request),
                "action": "POST",
                "types": ["application/json"]
            },
            {
                "rel": "self",
                "href": reverse('payment-detail', kwargs={'pk': obj.pk}, request=request),
                "action": "GET",
                "types": ["application/json"]
            },
            {
                "rel": "update",
                "href": reverse('payment-detail', kwargs={'pk': obj.pk}, request=request),
                "action": "PUT",
                "types": ["application/json"]
            },
            {
                "rel": "delete",
                "href": reverse('payment-detail', kwargs={'pk': obj.pk}, request=request),
                "action": "DELETE",
                "types": ["application/json"]
            }
        ]
