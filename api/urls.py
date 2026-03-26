from django.urls import path
from .views import current_lecture, mark_attendance, student_attendance_percentage, start_lecture
from .views import register_face
from .login import login
from .views import current_lecture, mark_attendance, student_attendance_percentage, start_lecture, register_face, lecture_attendance

urlpatterns = [
    path('lecture/<int:lecture_id>/attendance/', lecture_attendance),
    path('current-lecture/', current_lecture),
    path('start-lecture/', start_lecture),
    path('mark-attendance/', mark_attendance),
    path('student/<int:student_id>/attendance/', student_attendance_percentage),
    path('register-face/', register_face),
    path('login/', login),
]
