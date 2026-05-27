from django.db import models

from apps.common.models import TimeStampedModel


class EmailLog(TimeStampedModel):
    recipient = models.EmailField()
    template = models.CharField(max_length=120)
    status = models.CharField(max_length=30, default="pending")

    def __str__(self) -> str:
        return f"{self.template} -> {self.recipient}"
