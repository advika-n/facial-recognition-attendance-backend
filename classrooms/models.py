from django.db import models

class Classroom(models.Model):
    room_name = models.CharField(max_length=50, unique=True)
    room_type = models.CharField(max_length=20, choices=[('Lecture','Lecture'),('Lab','Lab')])
    camera_id = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.room_name