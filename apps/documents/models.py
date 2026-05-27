from django.db import models

from apps.common.models import TimeStampedModel


class GeneratedDocument(TimeStampedModel):
    quote_reference = models.CharField(max_length=50)
    file = models.FileField(upload_to="quotes/")
    document_type = models.CharField(max_length=30, default="quote_pdf")

    def __str__(self) -> str:
        return f"{self.document_type} - {self.quote_reference}"
