import json

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import TaskForm
from .models import Project, Task
from .views import dashboard, home, member_project_overview, project_create, project_detail, task_create, task_list

User = get_user_model()


class ProjectsTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.admin = User.objects.create_user(username='admin', password='AdminPass123', role='admin')
        self.tasker = User.objects.create_user(username='tasker', password='TaskerPass123', role='tasker')
        self.project = Project.objects.create(name='Test Project', description='Test description', owner=self.admin)
        self.project.members.add(self.tasker)
        self.task = Task.objects.create(
            project=self.project,
            title='Test Task',
            description='Task description',
            assignee=self.tasker,
            status='todo',
            due_date=timezone.now().date(),
        )

    def _setup_request(self, request, user=None):
        SessionMiddleware(get_response=lambda request: None).process_request(request)
        MessageMiddleware(get_response=lambda request: None).process_request(request)
        request.session.save()
        request.user = user or AnonymousUser()
        return request

    def test_dashboard_access(self):
        request = self.factory.get(reverse('dashboard'))
        request = self._setup_request(request, user=self.tasker)
        response = dashboard(request)
        self.assertEqual(response.status_code, 200)

    def test_home_public_for_logged_out_users(self):
        request = self.factory.get(reverse('home'))
        request = self._setup_request(request)
        response = home(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Plan, assign, and deliver projects with confidence.', response.content.decode('utf-8'))

    def test_home_redirects_taskers_to_task_list(self):
        request = self.factory.get(reverse('home'))
        request = self._setup_request(request, user=self.tasker)
        response = home(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('task_list'))

    def test_task_list_shows_assigned_tasks(self):
        request = self.factory.get(reverse('task_list'))
        request = self._setup_request(request, user=self.tasker)
        response = task_list(request)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('Your task workspace', content)
        self.assertIn('Test Task', content)

    def test_home_redirects_admins_to_dashboard(self):
        request = self.factory.get(reverse('home'))
        request = self._setup_request(request, user=self.admin)
        response = home(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('dashboard'))

    def test_admin_member_project_overview(self):
        request = self.factory.get(reverse('member_project_overview'))
        request = self._setup_request(request, user=self.admin)
        response = member_project_overview(request)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('Member project overview', content)
        self.assertIn('tasker', content)
        self.assertIn('Test Project', content)

    def test_tasker_cannot_view_member_project_overview(self):
        request = self.factory.get(reverse('member_project_overview'))
        request = self._setup_request(request, user=self.tasker)
        response = member_project_overview(request)
        self.assertEqual(response.status_code, 302)

    def test_project_detail_permission(self):
        request = self.factory.get(reverse('project_detail', kwargs={'pk': self.project.pk}))
        request = self._setup_request(request, user=self.tasker)
        response = project_detail(request, pk=self.project.pk)
        self.assertEqual(response.status_code, 200)

        other = User.objects.create_user(username='other', password='OtherPass123', role='tasker')
        request = self.factory.get(reverse('project_detail', kwargs={'pk': self.project.pk}))
        request = self._setup_request(request, user=other)
        response = project_detail(request, pk=self.project.pk)
        self.assertEqual(response.status_code, 302)

    def test_project_create_admin_only(self):
        request = self.factory.post(reverse('project_create'), {'name': 'New Project', 'description': 'New project description', 'members': [self.tasker.id]})
        request = self._setup_request(request, user=self.tasker)
        response = project_create(request)
        self.assertEqual(response.status_code, 302)

        request = self.factory.post(reverse('project_create'), {'name': 'New Project', 'description': 'New project description', 'members': [self.tasker.id]})
        request = self._setup_request(request, user=self.admin)
        response = project_create(request)
        self.assertEqual(response.status_code, 302)
        new_project = Project.objects.get(name='New Project')
        self.assertEqual(new_project.owner, self.admin)
        self.assertIn(self.tasker, new_project.members.all())

    def test_tasker_cannot_create_task(self):
        request = self.factory.post(reverse('task_create', kwargs={'pk': self.project.pk}), {
            'title': 'Unauthorized Task',
            'description': 'Should not be allowed',
            'assignee': self.tasker.pk,
            'status': 'todo',
            'due_date': timezone.now().date(),
            'time_spent_hours': '0',
        })
        request = self._setup_request(request, user=self.tasker)
        response = task_create(request, pk=self.project.pk)
        self.assertEqual(response.status_code, 302)

    def test_tasker_sees_only_assigned_tasks(self):
        other_tasker = User.objects.create_user(username='other_tasker', password='OtherPass123', role='tasker')
        self.project.members.add(other_tasker)
        Task.objects.create(
            project=self.project,
            title='Other Task',
            description='Not assigned to first tasker',
            assignee=other_tasker,
            status='todo',
            due_date=timezone.now().date(),
        )

        request = self.factory.get(reverse('project_detail', kwargs={'pk': self.project.pk}))
        request = self._setup_request(request, user=self.tasker)
        response = project_detail(request, pk=self.project.pk)
        content = response.content.decode('utf-8')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Test Task', content)
        self.assertNotIn('Other Task', content)

    def test_task_overdue_property(self):
        past_task = Task.objects.create(
            project=self.project,
            title='Past Task',
            due_date=timezone.now().date() - timezone.timedelta(days=2),
        )
        self.assertTrue(past_task.overdue)

    def test_multiple_taskers_on_project(self):
        tasker2 = User.objects.create_user(username='tasker2', password='Tasker2Pass123', role='tasker')
        self.project.members.add(tasker2)
        self.assertIn(tasker2, self.project.members.all())

        request = self.factory.get(reverse('project_detail', kwargs={'pk': self.project.pk}))
        request = self._setup_request(request, user=tasker2)
        response = project_detail(request, pk=self.project.pk)
        self.assertEqual(response.status_code, 200)

        form_data = {
            'title': 'New Multi-Tasker Task',
            'description': 'A task for the second tasker',
            'assignee': tasker2.pk,
            'status': 'todo',
            'due_date': timezone.now().date(),
            'time_spent_hours': '0',
        }
        form = TaskForm(project=self.project, data=form_data)
        self.assertTrue(form.is_valid())

    def test_api_projects_access(self):
        self.client.force_login(self.tasker)
        response = self.client.get(reverse('api_projects'))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIsInstance(payload, list)

    def test_api_create_project_admin(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse('api_projects'),
            data=json.dumps({'name': 'API Project', 'description': 'API project description'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['name'], 'API Project')

    def test_api_create_project_tasker_forbidden(self):
        self.client.force_login(self.tasker)
        response = self.client.post(
            reverse('api_projects'),
            data=json.dumps({'name': 'API Project', 'description': 'API project description'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 403)
