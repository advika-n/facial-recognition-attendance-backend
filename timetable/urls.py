from django.urls import path
from . import views

urlpatterns = [
    path('', views.timetable_list),
    path('<int:pk>/', views.timetable_detail),
]