from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('api/students/', include('students.urls')),
    path('api/professors/', include('professors.urls')),
    path('api/classrooms/', include('classrooms.urls')),
    path('api/timetable/', include('timetable.urls')),
    path('api/enrollments/', include('enrollments.urls')),
    path('api/reports/', include('attendance.urls')),
    path('api/classes/', include('lectures.urls')),
]