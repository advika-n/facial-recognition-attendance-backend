from django.db import models

class TimetableEntry(models.Model):
    class_id = models.CharField(max_length=50)
    course_name = models.CharField(max_length=100)
    slot_type = models.CharField(max_length=20)
    day = models.CharField(max_length=20)
    slot = models.CharField(max_length=10)
    classroom = models.CharField(max_length=50)

    class Meta:
        unique_together = ('day', 'slot', 'classroom')

    def __str__(self):
        return f"{self.class_id} | {self.day} {self.slot}"