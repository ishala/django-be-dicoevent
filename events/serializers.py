from rest_framework import serializers
from rest_framework.reverse import reverse
from .models import Event, EventPoster
from core.models import User

class EventSerializer(serializers.HyperlinkedModelSerializer):
    _links = serializers.SerializerMethodField()
    organizer_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Event
        fields = ['id', 'organizer_id', 'name', 'description',
                  'location', 'start_time', 'end_time', 'status',
                  'quota', 'category', '_links']

    def get__links(self, obj):
        request = self.context.get('request')
        return [
            {
                "rel": "self",
                "href": reverse('event-list', request=request),
                "action": "POST",
                "types": ["application/json"]
            },
            {
                "rel": "self",
                "href": reverse('event-detail', kwargs={'pk': obj.pk}, request=request),
                "action": "GET",
                "types": ["application/json"]
            },
            {
                "rel": "self",
                "href": reverse('event-detail', kwargs={'pk': obj.pk}, request=request),
                "action": "PUT",
                "types": ["application/json"]
            },
            {
                "rel": "self",
                "href": reverse('event-detail', kwargs={'pk': obj.pk}, request=request),
                "action": "DELETE",
                "types": ["application/json"]
            },
        ]

class EventPosterSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventPoster
        fields = ['id', 'event', 'image']
    
    def validate_image(self, value):
        max_size = 500 * 1024
        if value.size > max_size:
            raise serializers.ValidationError("Image size should not exceed 500KB.")
        return value