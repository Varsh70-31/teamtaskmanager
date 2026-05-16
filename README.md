# Team Task Manager

A professional Django-based project management app for teams.

## Features

- User authentication (signup, login, logout)
- Role-based user accounts: Admin / Member
- Project creation, team membership, and role-based permissions
- Task creation, assignment, status tracking, and overdue detection
- Clean dashboard with search, filters, and task progress metrics
- Responsive UI styled for a professional presentation
- SQLite database for local development
- REST-style JSON API endpoints for projects and task management
- Deployment-ready for Railway via `Procfile`

## Getting Started

1. Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Create a `.env` file from `.env.example` and set your secret key:

```powershell
copy .env.example .env
```

3. Install dependencies:

```powershell
pip install -r requirements.txt
```

4. Run database migrations:

```powershell
python manage.py migrate
```

5. Collect static files:

```powershell
python manage.py collectstatic --noinput
```

6. Start the development server:

```powershell
python manage.py runserver
```

7. Open the site at `http://127.0.0.1:8000/`.

> The first registered account becomes an admin user automatically. Subsequent signups are created as members.

## Deployment

This project includes a `Procfile` for Railway deployment and uses SQLite for the database.

### Railway setup

1. Create a Railway project and connect your GitHub repository.
2. Add environment variables:
   - `DJANGO_SECRET_KEY` — your production secret key
   - `DJANGO_DEBUG` — `False`
3. Railway will run the app using `Procfile`:
   - `web: gunicorn teamtaskmanager.wsgi --log-file -`
4. Make sure static files are collected in deployment.

See `DEPLOYMENT.md` for full deployment instructions.

## API Endpoints

- `GET /api/projects/` — list accessible projects
- `POST /api/projects/` — create a project (admin only)
- `GET /api/projects/<id>/` — project detail
- `GET /api/projects/<id>/tasks/` — list tasks in a project
- `POST /api/projects/<id>/tasks/` — create a task for a project
- `GET /api/tasks/<id>/` — get task detail
- `PUT /api/tasks/<id>/` — update a task
- `PATCH /api/tasks/<id>/` — partially update a task

## Next Steps

- Improve dashboard analytics with charts and progress visuals
- Add email notifications for overdue and assigned tasks
- Add role-specific team management pages
