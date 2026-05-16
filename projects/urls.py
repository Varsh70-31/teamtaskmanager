from django.urls import path
from . import views

urlpatterns = [
    # Move specific string endpoints to the top
    path('list/', views.project_list, name='project_list'),
    path('create/', views.project_create, name='project_create'),
    path('tasks/', views.task_list, name='task_list'),
    path('members/', views.member_project_overview, name='member_project_overview'),
    
    # URL parameters next
    path('<int:pk>/edit/', views.project_edit, name='project_edit'),
    path('<int:pk>/', views.project_detail, name='project_detail'),
    path('<int:pk>/tasks/create/', views.task_create, name='task_create'),
    path('tasks/<int:pk>/edit/', views.task_edit, name='task_edit'),
    
    # KEEP THIS AT THE BOTTOM: The catch-all empty path for projects dashboard
    path('', views.dashboard, name='dashboard'),
]