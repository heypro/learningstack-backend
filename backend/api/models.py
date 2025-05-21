# api/models.py
from django.db import models

class TelegramUser(models.Model):
    user_id      = models.BigIntegerField(primary_key=True)
    first_name   = models.CharField(max_length=128, blank=True)
    username     = models.CharField(max_length=128, blank=True)
    score        = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.username or self.first_name or str(self.user_id)
