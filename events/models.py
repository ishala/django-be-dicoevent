from django.db import models
from core.models import User
import uuid

# Create your models here.
class Event(models.Model):
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    organizer_id = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=120)
    description = models.TextField()
    location = models.CharField(max_length=30)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField()
    quota = models.IntegerField()
    category = models.CharField(null=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'events'

class EventPoster(models.Model):
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    image = models.ImageField()

    def __str__(self):
        return self.event.name

    class Meta:
        db_table = 'event_posters'