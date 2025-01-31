# pdfprocessor/models.py
import uuid
import os
from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

def validate_pdf(value):
    if not value.name.endswith('.pdf'):
        raise ValidationError('Only PDF files are allowed')

def user_pdf_upload_path(instance, filename):
    # Save files to: media/user_<id>/pdfs/<uuid>_<filename>
    return f'user_{instance.user.id}/pdfs/{uuid.uuid4()}_{filename}'

class PDFDocument(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    original_filename = models.CharField(max_length=255)
    uploaded_file = models.FileField(
        upload_to=user_pdf_upload_path,
        validators=[validate_pdf]
    )
    vector_db_path = models.CharField(max_length=500)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.pk:  # Only on creation
            self.original_filename = self.uploaded_file.name
            self.vector_db_path = os.path.join(
                settings.BASE_DIR,
                'vector_dbs',
                f'user_{self.user.id}',
                f'doc_{uuid.uuid4()}'
            )
        super().save(*args, **kwargs)