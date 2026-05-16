from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('signup/admin/', views.signup_view, {'role': 'admin'}, name='admin_signup'),
    path('signup/tasker/', views.signup_view, {'role': 'tasker'}, name='tasker_signup'),
    path('login/', views.login_view, name='login'),
    path('login/admin/', views.login_view, {'role': 'admin'}, name='admin_login'),
    path('login/tasker/', views.login_view, {'role': 'tasker'}, name='tasker_login'),
    path('logout/', views.logout_view, name='logout'),
]
