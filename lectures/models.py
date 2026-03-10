from django.db import models


class Course(models.Model):
    class_id = models.CharField(max_length=50, unique=True, default='')
    course_code = models.CharField(max_length=20, unique=True)
    course_name = models.CharField(max_length=100)
    professor_id = models.CharField(max_length=30, blank=True, default='')

    def __str__(self):
        return f"{self.course_code} - {self.course_name}"


class Teacher(models.Model):
    name = models.CharField(max_length=100)
    employee_id = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return f"{self.name} ({self.employee_id})"


class Lecture(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    classroom = models.CharField(max_length=50)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.course.course_code} | {self.classroom} | {self.date}"
