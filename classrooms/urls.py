from django.urls import path
from . import views

urlpatterns = [
    path('', views.classroom_list),
    path('<int:pk>/', views.classroom_detail),
]