import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from .forms import ProjectForm, TaskForm
from .models import Project, Task


def project_data(project):
    return {
        'id': project.pk,
        'name': project.name,
        'description': project.description,
        'owner': project.owner.username,
        'members': [member.username for member in project.members.all()],
        'created_at': project.created_at.isoformat(),
    }


def task_data(task):
    return {
        'id': task.pk,
        'title': task.title,
        'description': task.description,
        'project': task.project.pk,
        'project_name': task.project.name,
        'assignee': task.assignee.username if task.assignee else None,
        'status': task.status,
        'due_date': task.due_date.isoformat() if task.due_date else None,
        'time_spent_hours': float(task.time_spent_hours),
        'overdue': task.overdue,
    }


@login_required
@require_http_methods(['GET', 'POST'])
def api_projects(request):
    if request.method == 'GET':
        if request.user.role == 'admin':
            projects = Project.objects.all()
        else:
            projects = Project.objects.filter(members=request.user) | Project.objects.filter(owner=request.user)
            projects = projects.distinct()
        return JsonResponse([project_data(project) for project in projects], safe=False)

    payload = json.loads(request.body.decode('utf-8'))
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Only admin users can create projects.'}, status=403)

    form = ProjectForm(payload)
    if form.is_valid():
        project = form.save(commit=False)
        project.owner = request.user
        project.save()
        form.save_m2m()
        return JsonResponse(project_data(project), status=201)

    return JsonResponse({'errors': form.errors}, status=400)


@login_required
@require_http_methods(['GET'])
def api_project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.user.role != 'admin' and request.user != project.owner and request.user not in project.members.all():
        return JsonResponse({'error': 'Access denied.'}, status=403)
    return JsonResponse(project_data(project))


@login_required
@require_http_methods(['GET', 'POST'])
def api_project_tasks(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.user.role != 'admin' and request.user != project.owner and request.user not in project.members.all():
        return JsonResponse({'error': 'Access denied.'}, status=403)

    if request.method == 'GET':
        tasks = project.tasks.select_related('assignee').order_by('due_date')
        return JsonResponse([task_data(task) for task in tasks], safe=False)

    payload = json.loads(request.body.decode('utf-8'))
    form = TaskForm(payload, project=project)
    if form.is_valid():
        task = form.save(commit=False)
        task.project = project
        task.save()
        return JsonResponse(task_data(task), status=201)
    return JsonResponse({'errors': form.errors}, status=400)


@login_required
@require_http_methods(['GET', 'PUT', 'PATCH'])
def api_task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk)
    project = task.project
    if request.user.role != 'admin' and request.user != project.owner and request.user != task.assignee:
        return JsonResponse({'error': 'Access denied.'}, status=403)

    if request.method == 'GET':
        return JsonResponse(task_data(task))

    payload = json.loads(request.body.decode('utf-8'))
    restricted = request.user.role == 'tasker'
    form = TaskForm(payload, instance=task, project=project, restricted=restricted)
    if form.is_valid():
        task = form.save()
        return JsonResponse(task_data(task))
    return JsonResponse({'errors': form.errors}, status=400)
