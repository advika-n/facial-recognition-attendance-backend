from django.urls import path
from . import views

urlpatterns = [
    path('', views.enrollment_list),
    path('<int:pk>/', views.enrollment_detail),
]