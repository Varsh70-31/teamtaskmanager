from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render

from .forms import LoginForm, SignupForm
from .models import User


def signup_view(request, role=None):
    if role is None and request.method == 'GET':
        return render(request, 'accounts/signup_select.html')

    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            requested_role = form.cleaned_data.get('role')
            user.role = requested_role if requested_role in ['admin', 'tasker'] else 'tasker'
            user.save()
            messages.success(request, 'Account created successfully. Please log in.')
            return redirect('login')
    else:
        initial = {'role': role} if role in ['admin', 'tasker'] else {'role': 'tasker'}
        form = SignupForm(initial=initial)
    return render(request, 'accounts/signup.html', {'form': form})


def login_view(request, role=None):
    if request.user.is_authenticated:
        if request.user.role == 'admin':
            return redirect('dashboard')
        return redirect('task_list')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
            )
            requested_role = form.cleaned_data.get('role')
            if user is not None:
                # Only enforce role matching if a specific role was requested via URL
                if role is not None and user.role != requested_role:
                    messages.error(request, f'Please log in using the correct account type.')
                else:
                    login(request, user)
                    messages.success(request, 'Logged in successfully.')
                    if user.role == 'admin':
                        return redirect('dashboard')
                    return redirect('task_list')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        initial = {'role': role} if role in ['admin', 'tasker'] else {'role': 'tasker'}
        form = LoginForm(initial=initial)

    return render(request, 'accounts/login.html', {
        'form': form,
    })


def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('login')
