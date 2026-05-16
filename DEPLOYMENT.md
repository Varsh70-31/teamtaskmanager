# Railway Deployment Guide

This Django app is configured for Railway with:

- `railway.json` for build, pre-deploy, start, healthcheck, and restart settings
- Gunicorn as the production web server
- WhiteNoise for static files
- PostgreSQL through `DATABASE_URL`

## 1. Push the repo to GitHub

Commit your local changes and push them to GitHub.

```powershell
git add .
git commit -m "Prepare Railway deployment"
git push
```

## 2. Create the Railway project

1. Go to https://railway.com/.
2. Create a new project.
3. Choose **Deploy from GitHub repo**.
4. Select this repository.
5. If Railway asks for the root directory, use the folder that contains `manage.py`.

Railway detects Python/Django projects and builds them with Railpack.

## 3. Add PostgreSQL

In the Railway project canvas:

1. Click **Create**.
2. Choose **Database**.
3. Select **PostgreSQL**.

Then add this variable to the app service:

```text
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

## 4. Set app variables

Add these variables to the Django app service:

```text
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<generate-a-long-random-secret>
DJANGO_ALLOWED_HOSTS=.railway.app
DJANGO_CSRF_TRUSTED_ORIGINS=https://<your-generated-domain>
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

After Railway generates a public domain, replace `<your-generated-domain>` with the full domain, for example:

```text
DJANGO_CSRF_TRUSTED_ORIGINS=https://team-task-manager-production.up.railway.app
```

If you add a custom domain later, add it to both `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS`.

Optional hardening after the Railway domain is confirmed:

```text
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SECURE_HSTS_SECONDS=3600
```

Only increase HSTS once you are confident HTTPS works for every domain you serve.

## 5. Deploy

Railway will use `railway.json`:

- Build command: `python manage.py collectstatic --noinput`
- Pre-deploy command: `python manage.py migrate --noinput`
- Start command: `gunicorn teamtaskmanager.wsgi:application --bind 0.0.0.0:$PORT --log-file -`

The build step can run before database variables are available. The app allows `collectstatic` to run in that case, but `migrate` and the web process still require PostgreSQL on Railway.

Open the app service, click **Deploy**, and watch the deployment logs.

## 6. Create an admin user

After the app deploys, open a Railway shell for the app service and run:

```bash
python manage.py createsuperuser
```

You can also use the app signup flow. The first registered account becomes an admin.

## Troubleshooting

- If signup/login fails with `OperationalError: no such table: accounts_user`, the app is using an empty database or migrations did not run. Confirm the Django app service has `DATABASE_URL=${{Postgres.DATABASE_URL}}`, then redeploy so `python manage.py migrate --noinput` runs.
- If `collectstatic` succeeds but `migrate` fails with `Railway deployment requires DATABASE_URL`, add PostgreSQL and set `DATABASE_URL=${{Postgres.DATABASE_URL}}` on the Django app service.
- If CSS is missing, confirm the build ran `collectstatic` and that `whitenoise.middleware.WhiteNoiseMiddleware` is enabled.
- If POST forms fail with CSRF errors, update `DJANGO_CSRF_TRUSTED_ORIGINS` to include the exact `https://...` Railway or custom domain.
- If login or signup data disappears between deploys, confirm the app is using PostgreSQL through `DATABASE_URL`, not SQLite.
- If the app crashes on boot, check Railway logs for missing environment variables or failed migrations.

References:

- Railway Django guide: https://docs.railway.com/guides/django
- Railway config-as-code reference: https://docs.railway.com/config-as-code/reference
- Railway CLI deploy docs: https://docs.railway.com/cli/deploying
