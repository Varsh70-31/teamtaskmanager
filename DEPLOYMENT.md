# Railway Deployment Guide

This document outlines the steps to deploy the `team-task-manager` Django app to Railway.

## Pre-requisites

- A Railway account
- GitHub repository linked to the Railway project
- Your project code pushed to GitHub

## Railway configuration

1. Create a new Railway project and connect your GitHub repository.
2. In Railway, add the following environment variables:
   - `DJANGO_SECRET_KEY` — a secure random string
   - `DJANGO_DEBUG` — `False`
3. Make sure the deployment command is set by the `Procfile`:
   - `web: gunicorn teamtaskmanager.wsgi --log-file -`

## Local environment setup

1. Copy environment example to `.env`:

```powershell
copy .env.example .env
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Run the database migrations:

```powershell
python manage.py migrate
```

4. Collect static files:

```powershell
python manage.py collectstatic --noinput
```

## Important Railway notes

- Railway will use SQLite by default because the app is configured for SQLite.
- If you want a production database, configure a PostgreSQL plugin and update `DATABASES`.
- Ensure `DJANGO_SECRET_KEY` is not committed to GitHub.

## Verifying deployment

After Railway deploys successfully, open the live URL provided by Railway and verify:

- Signup and login work
- Dashboard loads
- Project and task pages are accessible
- The site serves static styles correctly

## Troubleshooting

- If static files fail, verify `STATICFILES_STORAGE` is set to `whitenoise.storage.CompressedManifestStaticFilesStorage`.
- If `DJANGO_DEBUG` is false and you see errors, check the Railway logs for details.
- Use `railway logs` or the Railway dashboard to inspect deployment errors.
