from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q

from .models import Project, Task

User = get_user_model()


class ProjectForm(forms.ModelForm):
    members = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'members-select'}),
    )

    class Meta:
        model = Project
        fields = ['name', 'description', 'members']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Project name'}),
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Brief project description...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure placeholders exist even when bound/initial data provided
        self.fields['name'].widget.attrs.setdefault('placeholder', 'Project name')
        self.fields['description'].widget.attrs.setdefault('placeholder', 'Brief project description...')


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'progress_note', 'assignee', 'status', 'due_date', 'time_spent_hours']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Task title'}),
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Detailed task description...'}),
            'progress_note': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Describe what you worked on...'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'placeholder': 'YYYY-MM-DD'}),
            'time_spent_hours': forms.NumberInput(attrs={'step': '0.25', 'min': '0', 'placeholder': '0.00'}),
        }

    def __init__(self, *args, project=None, restricted=False, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure placeholders for task fields
        if 'title' in self.fields:
            self.fields['title'].widget.attrs.setdefault('placeholder', 'Task title')
        if 'description' in self.fields:
            self.fields['description'].widget.attrs.setdefault('placeholder', 'Detailed task description...')
        if 'progress_note' in self.fields:
            self.fields['progress_note'].widget.attrs.setdefault('placeholder', 'Describe what you worked on...')
        if 'time_spent_hours' in self.fields:
            self.fields['time_spent_hours'].widget.attrs.setdefault('placeholder', '0.00')
        if restricted:
            self.fields = {
                'status': self.fields['status'],
                'progress_note': self.fields['progress_note'],
                'time_spent_hours': self.fields['time_spent_hours'],
            }
        else:
            if project:
                self.fields['assignee'].queryset = User.objects.filter(
                    Q(id=project.owner_id) | Q(pk__in=project.members.values_list('pk', flat=True))
                )
            else:
                self.fields['assignee'].queryset = User.objects.none()
