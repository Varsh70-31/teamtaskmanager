from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import ProjectForm, TaskForm
from .models import Project, Task

User = get_user_model()


def user_projects(user):
    if user.role == 'admin':
        return Project.objects.all()
    return Project.objects.filter(Q(members=user) | Q(owner=user)).distinct()


def task_workspace_context(request):
    projects = user_projects(request.user)
    status_filter = request.GET.get('status')
    today = timezone.now().date()
    week_end = today + timezone.timedelta(days=7)

    tasks = Task.objects.filter(project__in=projects).select_related('project', 'assignee')
    if request.user.role == 'tasker':
        tasks = tasks.filter(assignee=request.user)

    task_counts = tasks.aggregate(
        total=Count('id'),
        todo=Count('id', filter=Q(status='todo')),
        in_progress=Count('id', filter=Q(status='in_progress')),
        done=Count('id', filter=Q(status='done')),
        overdue=Count('id', filter=Q(status__in=['todo', 'in_progress'], due_date__lt=today)),
        due_this_week=Count('id', filter=Q(status__in=['todo', 'in_progress'], due_date__gte=today, due_date__lte=week_end)),
    )

    filtered_tasks = tasks
    if status_filter in ['todo', 'in_progress', 'done']:
        filtered_tasks = filtered_tasks.filter(status=status_filter)

    return {
        'task_counts': task_counts,
        'tasks': filtered_tasks.order_by('due_date', 'status')[:12],
        'overdue_tasks': tasks.filter(status__in=['todo', 'in_progress'], due_date__lt=today).order_by('due_date')[:6],
        'upcoming_tasks': tasks.filter(
            status__in=['todo', 'in_progress'],
            due_date__gte=today,
            due_date__lte=week_end,
        ).order_by('due_date')[:6],
        'status_filter': status_filter,
    }


def home(request):
    if not request.user.is_authenticated:
        return render(request, 'home.html')

    if request.user.role == 'admin':
        return redirect('dashboard')

    return redirect('task_list')


@login_required
def task_list(request):
    return render(request, 'projects/task_home.html', task_workspace_context(request))


@login_required
def member_project_overview(request):
    if request.user.role != 'admin':
        messages.error(request, 'Only admin users can view member project assignments.')
        return redirect('project_list')

    members = User.objects.filter(role='tasker').order_by('username')
    member_rows = []
    for member in members:
        assigned_tasks = Task.objects.filter(assignee=member).select_related('project')
        projects = Project.objects.filter(Q(members=member) | Q(tasks__assignee=member)).distinct().order_by('name')
        project_rows = []
        for project in projects:
            project_tasks = assigned_tasks.filter(project=project)
            totals = project_tasks.aggregate(
                total=Count('id'),
                todo=Count('id', filter=Q(status='todo')),
                in_progress=Count('id', filter=Q(status='in_progress')),
                done=Count('id', filter=Q(status='done')),
            )
            project_rows.append({
                'project': project,
                'counts': totals,
            })

        member_rows.append({
            'member': member,
            'projects': project_rows,
            'task_counts': assigned_tasks.aggregate(
                total=Count('id'),
                open=Count('id', filter=Q(status__in=['todo', 'in_progress'])),
                done=Count('id', filter=Q(status='done')),
            ),
        })

    return render(request, 'projects/member_project_overview.html', {
        'member_rows': member_rows,
    })


@login_required
def dashboard(request):
    projects = user_projects(request.user)
    status_filter = request.GET.get('status')
    today = timezone.now().date()
    week_end = today + timezone.timedelta(days=7)

    base_tasks = Task.objects.filter(project__in=projects)
    if request.user.role == 'tasker':
        base_tasks = base_tasks.filter(assignee=request.user)

    tasks = base_tasks
    if status_filter in ['todo', 'in_progress', 'done']:
        tasks = tasks.filter(status=status_filter)
    tasks = tasks.order_by('due_date')

    overdue_tasks = base_tasks.filter(status__in=['todo', 'in_progress'], due_date__lt=today).select_related('project', 'assignee')
    upcoming_tasks = base_tasks.filter(
        status__in=['todo', 'in_progress'],
        due_date__gte=today,
        due_date__lte=week_end,
    ).select_related('project', 'assignee').order_by('due_date')[:6]

    summary = base_tasks.aggregate(
        total=Count('id'),
        todo=Count('id', filter=Q(status='todo')),
        in_progress=Count('id', filter=Q(status='in_progress')),
        done=Count('id', filter=Q(status='done')),
        overdue=Count('id', filter=Q(status__in=['todo', 'in_progress'], due_date__lt=today)),
        due_this_week=Count('id', filter=Q(status__in=['todo', 'in_progress'], due_date__gte=today, due_date__lte=week_end)),
        unassigned=Count('id', filter=Q(assignee__isnull=True)),
        total_hours=Sum('time_spent_hours'),
    )
    progress = int(summary['done'] / summary['total'] * 100) if summary['total'] else 0
    open_tasks = (summary['todo'] or 0) + (summary['in_progress'] or 0)
    schedule_pressure = (summary['overdue'] or 0) + (summary['due_this_week'] or 0)

    def percent(part, whole):
        return int((part or 0) / whole * 100) if whole else 0
    
    status_total = summary['total'] or 0
    status_segments = [
        {'label': 'To Do', 'count': summary['todo'] or 0, 'percent': percent(summary['todo'], status_total), 'class_name': 'todo'},
        {'label': 'In Progress', 'count': summary['in_progress'] or 0, 'percent': percent(summary['in_progress'], status_total), 'class_name': 'in-progress'},
        {'label': 'Done', 'count': summary['done'] or 0, 'percent': percent(summary['done'], status_total), 'class_name': 'done'},
    ]

    open_later = max(open_tasks - schedule_pressure, 0)
    schedule_total = (summary['overdue'] or 0) + (summary['due_this_week'] or 0) + open_later + (summary['done'] or 0)
    schedule_segments = [
        {'label': 'Overdue', 'count': summary['overdue'] or 0, 'percent': percent(summary['overdue'], schedule_total), 'class_name': 'overdue'},
        {'label': 'Due this week', 'count': summary['due_this_week'] or 0, 'percent': percent(summary['due_this_week'], schedule_total), 'class_name': 'due-soon'},
        {'label': 'Open later', 'count': open_later, 'percent': percent(open_later, schedule_total), 'class_name': 'todo'},
        {'label': 'Done', 'count': summary['done'] or 0, 'percent': percent(summary['done'], schedule_total), 'class_name': 'done'},
    ]

    time_summary = base_tasks.aggregate(
        todo_hours=Sum('time_spent_hours', filter=Q(status='todo')),
        in_progress_hours=Sum('time_spent_hours', filter=Q(status='in_progress')),
        done_hours=Sum('time_spent_hours', filter=Q(status='done')),
    )
    time_rows = [
        {'label': 'To Do', 'hours': float(time_summary['todo_hours'] or 0), 'class_name': 'todo'},
        {'label': 'In Progress', 'hours': float(time_summary['in_progress_hours'] or 0), 'class_name': 'in-progress'},
        {'label': 'Done', 'hours': float(time_summary['done_hours'] or 0), 'class_name': 'done'},
    ]
    max_hours = max([row['hours'] for row in time_rows] + [1])
    for row in time_rows:
        row['percent'] = percent(row['hours'], max_hours)
    
    # Get top projects by task count and status mix.
    project_tasks = Project.objects.filter(pk__in=projects).annotate(
        task_count=Count('tasks'),
        todo_count=Count('tasks', filter=Q(tasks__status='todo')),
        in_progress_count=Count('tasks', filter=Q(tasks__status='in_progress')),
        done_count=Count('tasks', filter=Q(tasks__status='done')),
        overdue_count=Count('tasks', filter=Q(tasks__status__in=['todo', 'in_progress'], tasks__due_date__lt=today)),
    ).order_by('-task_count')[:5]
    
    project_rows = []
    for project in project_tasks:
        completion = int(project.done_count / project.task_count * 100) if project.task_count else 0
        project.completion = completion
        project.todo_percent = percent(project.todo_count, project.task_count)
        project.in_progress_percent = percent(project.in_progress_count, project.task_count)
        project.done_percent = percent(project.done_count, project.task_count)
        project_rows.append(project)

    assignee_rows = base_tasks.values('assignee__username').annotate(
        total=Count('id'),
        open_count=Count('id', filter=Q(status__in=['todo', 'in_progress'])),
        overdue_count=Count('id', filter=Q(status__in=['todo', 'in_progress'], due_date__lt=today)),
    ).order_by('-open_count', '-total')[:6]
    max_open_count = max([row['open_count'] for row in assignee_rows] + [1])
    workload_rows = []
    for row in assignee_rows:
        workload_rows.append({
            'label': row['assignee__username'] or 'Unassigned',
            'total': row['total'],
            'open_count': row['open_count'],
            'overdue_count': row['overdue_count'],
            'open_percent': percent(row['open_count'], max_open_count),
            'overdue_percent': percent(row['overdue_count'], max_open_count),
        })
    
    return render(request, 'projects/dashboard.html', {
        'projects': projects,
        'tasks': tasks.select_related('project', 'assignee')[:8],
        'overdue_tasks': overdue_tasks[:6],
        'upcoming_tasks': upcoming_tasks,
        'project_rows': project_rows,
        'status_segments': status_segments,
        'schedule_segments': schedule_segments,
        'time_rows': time_rows,
        'workload_rows': workload_rows,
        'summary': summary,
        'status_filter': status_filter,
        'progress': progress,
        'open_tasks': open_tasks,
        'schedule_pressure': schedule_pressure,
    })


@login_required
def project_list(request):
    query = request.GET.get('q', '').strip()
    projects = user_projects(request.user)
    if query:
        projects = projects.filter(Q(name__icontains=query) | Q(description__icontains=query))
    
    # Annotate projects with task status counts
    projects = projects.annotate(
        total_tasks=Count('tasks'),
        todo_count=Count('tasks', filter=Q(tasks__status='todo')),
        in_progress_count=Count('tasks', filter=Q(tasks__status='in_progress')),
        done_count=Count('tasks', filter=Q(tasks__status='done')),
    )
    
    # Calculate percentages for status bar
    for project in projects:
        if project.total_tasks > 0:
            project.todo_percent = int((project.todo_count / project.total_tasks) * 100)
            project.in_progress_percent = int((project.in_progress_count / project.total_tasks) * 100)
            project.done_percent = int((project.done_count / project.total_tasks) * 100)
    
    return render(request, 'projects/project_list.html', {'projects': projects, 'query': query})


@login_required
def project_create(request):
    if request.user.role != 'admin':
        messages.error(request, 'Only admin users can create new projects.')
        return redirect('project_list')

    form = ProjectForm(request.POST or None)
    if form.is_valid():
        project = form.save(commit=False)
        project.owner = request.user
        project.save()
        form.save_m2m()
        messages.success(request, 'Project created successfully.')
        return redirect('project_detail', pk=project.pk)

    return render(request, 'projects/project_form.html', {'form': form, 'title': 'Create Project'})


@login_required
def project_edit(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.user != project.owner and request.user.role != 'admin':
        messages.error(request, 'You do not have permission to update this project.')
        return redirect('project_detail', pk=pk)

    form = ProjectForm(request.POST or None, instance=project)
    if form.is_valid():
        form.save()
        messages.success(request, 'Project updated successfully.')
        return redirect('project_detail', pk=project.pk)

    return render(request, 'projects/project_form.html', {'form': form, 'title': 'Edit Project'})


@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.user != project.owner and request.user not in project.members.all():
        messages.error(request, 'You are not assigned to this project.')
        return redirect('project_list')

    tasks = project.tasks.select_related('assignee').order_by('due_date')
    if request.user.role == 'tasker':
        tasks = tasks.filter(assignee=request.user)
    can_manage_project = request.user.role == 'admin'
    can_create_task = request.user.role == 'admin'
    return render(request, 'projects/project_detail.html', {
        'project': project,
        'tasks': tasks,
        'can_manage_project': can_manage_project,
        'can_create_task': can_create_task,
    })


@login_required
def task_create(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.user.role != 'admin':
        messages.error(request, 'Only admins can create tasks.')
        return redirect('project_detail', pk=pk)

    form = TaskForm(request.POST or None, project=project)
    if form.is_valid():
        task = form.save(commit=False)
        task.project = project
        task.save()
        messages.info(request, 'Task created successfully.')
        return redirect('project_detail', pk=pk)

    return render(request, 'projects/task_form.html', {'form': form, 'project': project, 'title': 'New Task'})


@login_required
def task_edit(request, pk):
    task = get_object_or_404(Task, pk=pk)
    project = task.project
    if request.user.role == 'tasker':
        if request.user != task.assignee:
            messages.error(request, 'You do not have permission to update this task.')
            return redirect('project_detail', pk=project.pk)
        form = TaskForm(request.POST or None, instance=task, project=project, restricted=True)
    else:
        if request.user != project.owner and request.user.role != 'admin':
            messages.error(request, 'You do not have permission to edit this task.')
            return redirect('project_detail', pk=project.pk)
        form = TaskForm(request.POST or None, instance=task, project=project)

    if form.is_valid():
        form.save()
        messages.info(request, 'Task updated successfully.')
        return redirect('project_detail', pk=project.pk)

    return render(request, 'projects/task_form.html', {'form': form, 'project': project, 'task': task, 'title': 'Edit Task'})
