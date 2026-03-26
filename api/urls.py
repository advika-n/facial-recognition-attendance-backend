from django.urls import path
from .views import (
    current_lecture, start_lecture, mark_attendance,
    lecture_attendance, student_attendance_percentage,
    register_face, get_encodings, recognize_and_mark
)
from .login import login

urlpatterns = [
    path('current-lecture/', current_lecture),
    path('start-lecture/', start_lecture),
    path('mark-attendance/', mark_attendance),
    path('recognize-and-mark/', recognize_and_mark),
    path('lecture/<int:lecture_id>/attendance/', lecture_attendance),
    path('student/<int:student_id>/attendance/', student_attendance_percentage),
    path('register-face/', register_face),
    path('get-encodings/', get_encodings),
    path('login/', login),
]
