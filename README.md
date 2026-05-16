# Team Task Manager

A Django-based team task management app for coordinating projects, assigning work, and tracking delivery progress.

## Features

- Signup, login, logout, and custom user roles
- Admin and tasker experiences with role-specific navigation
- Admin dashboard with workload, schedule, status, and project metrics
- Project creation, editing, membership, and ownership controls
- Task creation, assignment, status updates, due dates, and time tracking
- Tasker workspace for assigned tasks only
- Member overview page for admins
- Responsive dark UI with mobile-friendly navigation
- REST-style JSON API for projects and tasks
- Railway-ready deployment with Gunicorn, WhiteNoise, PostgreSQL, and config-as-code

## Tech Stack

- Python 3.12
- Django 4.2
- SQLite for local development
- PostgreSQL for Railway production deployments
- Gunicorn
- WhiteNoise
- Railway Railpack

## Local Setup

From the project root, the folder that contains `manage.py`:

```powershell
cd team-task-manager
```

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Create a local `.env` file:

```powershell
copy .env.example .env
```

For local development, keep or set:

```text
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=replace-with-a-secure-local-key
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
```

Run migrations:

```powershell
python manage.py migrate
```

Start the development server:

```powershell
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

The first registered account becomes an admin automatically. Later signups become tasker accounts.

## Useful Commands

Run checks:

```powershell
python manage.py check
```

Run tests:

```powershell
python manage.py test
```

Collect static files:

```powershell
python manage.py collectstatic --noinput
```

Create a superuser:

```powershell
python manage.py createsuperuser
```

## Main Pages

- `/` - home, redirects authenticated users to their role workspace
- `/accounts/login/` - login
- `/accounts/signup/` - signup
- `/projects/` - admin dashboard
- `/projects/list/` - project portfolio
- `/projects/tasks/` - tasker task workspace
- `/projects/members/` - admin member overview
- `/projects/<id>/` - project detail

## API Endpoints

- `GET /api/projects/` - list accessible projects
- `POST /api/projects/` - create a project, admin only
- `GET /api/projects/<id>/` - project detail
- `GET /api/projects/<id>/tasks/` - list tasks in a project
- `POST /api/projects/<id>/tasks/` - create a task in a project
- `GET /api/tasks/<id>/` - task detail
- `PUT /api/tasks/<id>/` - update a task
- `PATCH /api/tasks/<id>/` - partially update a task

## Environment Variables

Local variables are loaded from `.env`. Railway variables are configured in the Railway dashboard.

```text
DJANGO_SECRET_KEY=<secret-key>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=.railway.app
DJANGO_CSRF_TRUSTED_ORIGINS=https://your-app.up.railway.app
DJANGO_SECURE_SSL_REDIRECT=False
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
DJANGO_SECURE_HSTS_SECONDS=0
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

`DATABASE_URL` is optional locally. If it is not set, the app uses SQLite at `db.sqlite3`.

## Railway Deployment

This repo includes:

- `railway.json` for Railway build and deploy settings
- `Procfile` as a compatible Gunicorn start command
- `runtime.txt` for Python version selection
- `DEPLOYMENT.md` with the full deployment walkthrough

Railway deploy flow:

1. Push this repository to GitHub.
2. Create a Railway project.
3. Deploy from the GitHub repo.
4. Add a PostgreSQL service.
5. Set the app environment variables.
6. Generate a Railway domain.
7. Update `DJANGO_CSRF_TRUSTED_ORIGINS` with the generated `https://...` domain.
8. Redeploy.

Railway uses `railway.json` to run:

```bash
python manage.py collectstatic --noinput
python manage.py migrate --noinput
gunicorn teamtaskmanager.wsgi:application --bind 0.0.0.0:$PORT --log-file -
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for the detailed Railway guide.

## Notes

- The app is designed for role-based project management, not public anonymous project access.
- Taskers only see tasks assigned to them.
- Admin users manage projects, tasks, and member assignments.
- Do not commit `.env`, `db.sqlite3`, or `staticfiles/`.
