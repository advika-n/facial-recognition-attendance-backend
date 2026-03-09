from django.db import models

class Professor(models.Model):
    professor_id = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100)
    department = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.professor_id} - {self.name}"