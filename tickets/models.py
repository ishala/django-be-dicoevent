from django.db import models
from events.models import Event
from core.models import User
import uuid

# Create your models here.
class Ticket(models.Model):
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    event_id = models.ForeignKey(Event, on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    price = models.IntegerField()
    sales_start = models.DateTimeField()
    sales_end = models.DateTimeField()
    quota = models.IntegerField()

    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'tickets'