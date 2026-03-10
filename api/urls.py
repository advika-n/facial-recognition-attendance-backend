from django.urls import path
from .views import current_lecture, mark_attendance, student_attendance_percentage
from .views import register_face
from .login import login

urlpatterns = [
    path('current-lecture/', current_lecture),
    path('mark-attendance/', mark_attendance),
    path('student/<int:student_id>/attendance/', student_attendance_percentage),
    path('register-face/', register_face),
    path('login/', login),
]
