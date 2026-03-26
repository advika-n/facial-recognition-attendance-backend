from django.db import models


class Student(models.Model):
    name = models.CharField(max_length=100)
    registration_number = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=50, blank=True, default='')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.registration_number} - {self.name}"
