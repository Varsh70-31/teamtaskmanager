from django.contrib import admin
from django.urls import include, path

from projects import views as project_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', project_views.home, name='home'),
    path('accounts/', include('accounts.urls')),
    path('projects/', include('projects.urls')),
    path('api/', include('projects.api_urls')),
]
