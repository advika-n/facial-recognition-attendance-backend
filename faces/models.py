from django.db import models
from students.models import Student

class FaceEncoding(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="face_encodings"
    )
    encoding = models.BinaryField()
    label = models.CharField(max_length=50, blank=True, default='')  # e.g. "straight", "left", "right"
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"FaceEncoding ({self.label}) for {self.student.registration_number}"
