# Attendly

Attendly is a web-based attendance management system for teachers and students. It helps teachers manage courses and timetables, open short-lived attendance sessions, and review attendance reports. Students can join courses, view their schedules, and mark attendance using a secure attendance code combined with location verification.

## Live application

[Open Attendly](https://attendance-tracker-two-nu.vercel.app/)

## Features

### Students

- Register with email OTP verification.
- Join courses using a teacher-provided join code.
- View enrolled courses and weekly timetables.
- Mark attendance using a six-digit session code.
- Share browser location during check-in to verify that they are within the teacher's attendance zone.
- View course-level and overall attendance percentages.
- Configure reminder emails and change their password.

### Teachers

- Register with email OTP verification.
- Create courses and timetable slots.
- Generate and regenerate course join codes.
- Open one-minute attendance sessions during active timetable slots.
- Set the attendance-zone radius when opening a session.
- Share browser location so the session is tied to the classroom location.
- Review attendance reports for enrolled students.

## How attendance works

Attendance is recorded only when all of these checks pass:

1. The student enters the correct six-digit attendance code.
2. The session is still open and has not expired.
3. The student is actively enrolled in the course.
4. The student's browser location is within the teacher's configured radius.
5. The device has not already been used by another account for that session.

Attendance sessions expire after one minute. Student latitude and longitude are stored with geofenced attendance records for verification and reporting.

## Device fingerprint protection

The frontend creates a lightweight device fingerprint from browser metadata such as the user agent, language, screen size, color depth, timezone, and storage availability. The backend hashes this value with SHA-256 before storing it.

If the same device fingerprint is used by another account for the same course session, the second attendance attempt is rejected. This is an abuse-prevention measure, not a replacement for authentication: browser fingerprints can change or be spoofed.

## Architecture

```text
React/Vite frontend on Vercel
              |
              v
Django REST API on PythonAnywhere
              |
              +--> SQLite database
              +--> Gmail SMTP for OTPs and reminders

GitHub Actions every 15 minutes
              |
              v
Protected scheduler endpoint
              |
              +--> Finalize absent attendance records
              +--> Send schedule and late-attendance reminders
```

## Project structure

```text
backend/
  manage.py
  website/                 Django project settings and URLs
  mysite/                  Models, API views, serializers, commands, and tests

frontend/my-react-app/
  src/App.jsx              React application and dashboards
  src/api.js               API client and JWT handling
  src/geofenceUtils.js     Browser geolocation and device fingerprint utilities

.github/workflows/
  scheduled-tasks.yml      Scheduled backend task trigger
```

## Local development

### Backend

Requirements: Python 3.12+ recommended.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

The backend runs at `http://127.0.0.1:8000`. With `DEBUG=True` and no SMTP credentials, emails are printed to the development console.

### Frontend

```powershell
cd frontend\my-react-app
npm install
npm run dev
```

The frontend uses `http://<current-host>:8000/api` by default. To configure another API, create a frontend `.env` file with:

```text
VITE_API_URL=https://your-backend-host.example/api
```

## Production deployment

### Backend on PythonAnywhere

1. Clone the repository and install the backend requirements.
2. Run `python manage.py migrate` and `python manage.py collectstatic --noinput`.
3. Configure the PythonAnywhere WSGI file to use `website.settings`.
4. Set the following environment variables:

```text
DJANGO_SECRET_KEY=<long random value>
DEBUG=False
ALLOWED_HOSTS=<your-pythonanywhere-host>
CORS_ALLOWED_ORIGINS=https://attendance-tracker-two-nu.vercel.app
CSRF_TRUSTED_ORIGINS=https://attendance-tracker-two-nu.vercel.app
TIME_ZONE=Asia/Kolkata
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=<gmail address>
EMAIL_HOST_PASSWORD=<gmail app password>
DEFAULT_FROM_EMAIL=<gmail address>
SCHEDULER_SECRET=<random value of at least 32 characters>
```

Use a Gmail App Password rather than a normal Gmail password. Never commit `.env` files, passwords, or provider tokens.

### Frontend on Vercel

Set the Vercel project root to `frontend/my-react-app` and configure:

```text
Build command: npm run build
Output directory: dist
VITE_API_URL=https://<your-pythonanywhere-host>/api
```

The SPA rewrite is configured in `frontend/my-react-app/vercel.json`.

### Scheduled tasks

Add these GitHub repository Actions secrets:

```text
BACKEND_CRON_URL=https://<your-pythonanywhere-host>/api/internal/scheduled-tasks/
SCHEDULER_SECRET=<the same value configured on the backend>
```

The workflow in `.github/workflows/scheduled-tasks.yml` calls the protected endpoint every 15 minutes. It runs the `finalize_attendance` and `send_reminders` Django management commands. It can also be started manually from the GitHub Actions tab.

## Verification commands

```powershell
cd backend
$env:DEBUG='True'
python manage.py check
python manage.py test

cd ..\frontend\my-react-app
npm run lint
npm run build
```

## Security notes

- Use HTTPS in production because browser geolocation requires a secure context.
- Keep Django, Gmail, scheduler, and hosting credentials out of Git.
- The scheduler endpoint requires the `X-Scheduler-Secret` header.
- SQLite is suitable for this small demonstration deployment; larger installations should use a production database.
