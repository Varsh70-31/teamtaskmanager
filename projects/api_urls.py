from django.urls import path

from . import api_views

urlpatterns = [
    path('projects/', api_views.api_projects, name='api_projects'),
    path('projects/<int:pk>/', api_views.api_project_detail, name='api_project_detail'),
    path('projects/<int:pk>/tasks/', api_views.api_project_tasks, name='api_project_tasks'),
    path('tasks/<int:pk>/', api_views.api_task_detail, name='api_task_detail'),
]
