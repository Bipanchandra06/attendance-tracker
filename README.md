# Attendly deployment guide

Attendly is a React/Vite frontend with a Django REST API. The recommended free demo deployment is:

```text
Vercel React frontend → Render Django API → Neon PostgreSQL
                                      ↘ Gmail API
GitHub Actions runs reminder and absence commands every 15 minutes.
```

The production database starts empty. No demo passwords or pre-created users are committed.

## Local development

```powershell
Copy-Item .env.example backend\.env
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

In a second terminal:

```powershell
cd frontend\my-react-app
npm install
npm run dev
```

When Gmail credentials are absent and `DEBUG=True`, emails are printed through Django’s console email backend. Production requires Gmail API credentials.

## Gmail API setup

1. Create or use a separate Gmail account for this demo.
2. Create a Google Cloud project and enable the Gmail API.
3. Create OAuth credentials for a desktop application.
4. Download the client secret JSON locally; do not commit it.
5. Generate an offline refresh token:

   ```powershell
   pip install -r backend\requirements.txt
   python scripts\generate_gmail_token.py path\to\client_secret.json
   ```

6. Store the printed values as Render environment variables and GitHub repository secrets:

   ```text
   GMAIL_CLIENT_ID
   GMAIL_CLIENT_SECRET
   GMAIL_REFRESH_TOKEN
   GMAIL_SENDER_EMAIL
   ```

Never put these values in `VITE_*` variables or frontend source code. To revoke access, remove the OAuth client/token in Google Cloud and create a new token.

## Neon database

1. Create a Neon PostgreSQL project.
2. Copy its SSL connection string into `DATABASE_URL`.
3. Use the same value in Render and GitHub Actions secrets.
4. Run migrations after deployment:

   ```text
   python manage.py showmigrations
   python manage.py migrate
   ```

Production uses PostgreSQL whenever `DATABASE_URL` exists. Local development falls back to SQLite when it does not.

## Render API deployment

The repository includes `render.yaml`. Connect the public GitHub repository to Render and deploy the blueprint.

The service uses:

```text
Root directory: backend
Build command: pip install -r requirements.txt && python manage.py collectstatic --noinput
Start command: python manage.py migrate && gunicorn website.wsgi:application --bind 0.0.0.0:$PORT
Health check: /api/health/
```

Configure these environment variables in Render:

```text
DEBUG=False
DJANGO_SECRET_KEY=<new random secret>
DATABASE_URL=<Neon SSL URL>
ALLOWED_HOSTS=<exact Render hostname>
CORS_ALLOWED_ORIGINS=https://<exact Vercel hostname>
CSRF_TRUSTED_ORIGINS=https://<exact Vercel hostname>
TIME_ZONE=Asia/Kolkata
GMAIL_CLIENT_ID=<secret>
GMAIL_CLIENT_SECRET=<secret>
GMAIL_REFRESH_TOKEN=<secret>
GMAIL_SENDER_EMAIL=<demo Gmail address>
```

The free Render API may sleep after inactivity and take about one minute to wake up. This is expected for this interviewer-focused deployment. The local filesystem is not used for production data.

## Vercel frontend deployment

Create a Vercel project connected to the repository with:

```text
Root directory: frontend/my-react-app
Build command: npm run build
Output directory: dist
```

Set this Vercel environment variable:

```text
VITE_API_URL=https://<exact Render hostname>/api
```

`frontend/my-react-app/vercel.json` rewrites direct SPA routes to `index.html`.

## GitHub scheduled tasks

`.github/workflows/scheduled-tasks.yml` runs every 15 minutes and also supports manual `workflow_dispatch`.

Add these GitHub repository secrets:

```text
DATABASE_URL
DJANGO_SECRET_KEY
GMAIL_CLIENT_ID
GMAIL_CLIENT_SECRET
GMAIL_REFRESH_TOKEN
GMAIL_SENDER_EMAIL
```

The workflow runs:

```text
python backend/manage.py finalize_attendance
python backend/manage.py send_reminders
```

GitHub scheduled jobs may start later than their scheduled time. `ReminderLog` makes reminder delivery idempotent, so a delayed or repeated run will not send duplicates.

## Interviewer demo flow

1. Register a teacher account.
2. Verify the teacher through Gmail OTP.
3. Log in as teacher.
4. Create a course.
5. Add a timetable slot for the current day and time.
6. Open a second browser or incognito window.
7. Register a student account.
8. Verify the student through Gmail OTP.
9. Join the teacher’s course using the generated join code.
10. Return to the teacher window and open the attendance code.
11. Enter the code as the student.
12. View the student attendance percentage.
13. View the teacher attendance report.
14. Trigger the GitHub Actions workflow manually to demonstrate scheduled services.

## Verification commands

```powershell
cd backend
python manage.py check
python manage.py test

cd ..\frontend\my-react-app
npm run lint
npm run build
```

Free-tier hosting is intended here for demonstration, not real production traffic. Gmail account quotas, Render cold starts, Neon limits, and GitHub schedule delays still apply.
