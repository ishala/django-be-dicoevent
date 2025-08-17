from django.db import models
from core.models import User
from tickets.models import Ticket
import uuid

# Create your models here.
class Registration(models.Model):
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    ticket_id = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        db_table = 'registrations'
        unique_together = ('id', 'ticket_id', 'user_id')

class Payment(models.Model):
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    registration_id = models.ForeignKey(Registration, on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=20)
    payment_status = models.CharField(max_length=15)
    amount_paid = models.IntegerField()

    def __str__(self):
        return f'{self.payment_method} is {self.payment_status}'

    class Meta:
        db_table = 'payments'