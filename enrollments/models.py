from django.db import models
from students.models import Student
from lectures.models import Course, Teacher

class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    class Meta:
        unique_together = ('student', 'course', 'teacher')

    def __str__(self):
        teacher_name = self.teacher.name if self.teacher else "No teacher"
        return f"{self.student.registration_number} → {self.course.course_code} ({teacher_name})"
