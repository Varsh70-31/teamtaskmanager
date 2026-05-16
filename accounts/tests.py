from django.contrib.auth import authenticate
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase
from django.urls import reverse

from .models import User
from .views import login_view, signup_view


class AccountsTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _setup_request(self, request):
        SessionMiddleware(get_response=lambda request: None).process_request(request)
        MessageMiddleware(get_response=lambda request: None).process_request(request)
        request.session.save()
        request.user = AnonymousUser()
        return request

    def test_first_user_created_as_admin(self):
        request = self.factory.post(
            reverse('signup'),
            {
                'username': 'adminuser',
                'email': 'admin@example.com',
                'role': 'admin',
                'password1': 'StrongPass123',
                'password2': 'StrongPass123',
            },
        )
        self._setup_request(request)
        response = signup_view(request)
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username='adminuser')
        self.assertEqual(user.role, 'admin')

    def test_second_user_created_as_tasker(self):
        User.objects.create_user(username='existing', email='existing@example.com', password='StrongPass123', role='admin')
        request = self.factory.post(
            reverse('signup'),
            {
                'username': 'taskeruser',
                'email': 'tasker@example.com',
                'role': 'tasker',
                'password1': 'StrongPass123',
                'password2': 'StrongPass123',
            },
        )
        self._setup_request(request)
        response = signup_view(request)
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username='taskeruser')
        self.assertEqual(user.role, 'tasker')

    def test_tasker_login_redirects_to_home_tasks(self):
        User.objects.create_user(username='taskeruser', email='tasker@example.com', password='StrongPass123', role='tasker')
        request = self.factory.post(reverse('tasker_login'), {'username': 'taskeruser', 'password': 'StrongPass123', 'role': 'tasker'})
        self._setup_request(request)
        response = login_view(request, role='tasker')
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('task_list'), response['Location'])

    def test_admin_login_redirects_to_dashboard(self):
        User.objects.create_user(username='adminuser', email='admin@example.com', password='StrongPass123', role='admin')
        request = self.factory.post(reverse('admin_login'), {'username': 'adminuser', 'password': 'StrongPass123', 'role': 'admin'})
        self._setup_request(request)
        response = login_view(request, role='admin')
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('dashboard'), response['Location'])
