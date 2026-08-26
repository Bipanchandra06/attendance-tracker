# Attendly: free interviewer deployment

Attendly uses this no-card demo architecture:

```text
Vercel React frontend → PythonAnywhere Django API → SQLite
                                      ↘ Gmail SMTP
GitHub Actions calls the protected scheduler endpoint every 15 minutes.
```

The production database starts empty. Do not commit demo passwords, `.env` files, Gmail app passwords, or provider tokens.

## 1. Push the repository to GitHub

Create a public GitHub repository and push the project:

```powershell
git remote set-url origin https://github.com/YOUR_USERNAME/attendance-tracker.git
git add .
git commit -m "Prepare Attendly for free deployment"
git push -u origin main
```

## 2. Create a Gmail App Password

Use a separate Gmail account for the demo.

1. Enable 2-Step Verification on the Gmail account.
2. Open Google Account → Security → App passwords.
3. Create an app password named `Attendly`.
4. Copy the generated 16-character password.

Use the app password, not the normal Gmail password. Gmail app passwords require 2-Step Verification: https://support.google.com/mail/answer/185833

## 3. Deploy the backend to PythonAnywhere

Create a free PythonAnywhere account and a web app using the Python version supported by the account.

In a PythonAnywhere Bash console:

```bash
git clone https://github.com/YOUR_USERNAME/attendance-tracker.git
cd attendance-tracker/backend
python3 -m venv ~/.virtualenvs/attendly
source ~/.virtualenvs/attendly/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

Set the web app’s virtualenv to:

```text
/home/YOUR_PYTHONANYWHERE_USERNAME/.virtualenvs/attendly
```

Set the web app source directory to:

```text
/home/YOUR_PYTHONANYWHERE_USERNAME/attendance-tracker/backend
```

Edit the PythonAnywhere WSGI file and replace its contents with the following. If the free-account interface has an environment-variable section, use that instead; never commit the values below to GitHub.

```python
import os
import sys

project_path = '/home/YOUR_PYTHONANYWHERE_USERNAME/attendance-tracker/backend'
if project_path not in sys.path:
    sys.path.insert(0, project_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')

os.environ.update({
    'DJANGO_SECRET_KEY': 'paste-a-long-random-secret-here',
    'DEBUG': 'False',
    'ALLOWED_HOSTS': 'YOUR_USERNAME.pythonanywhere.com',
    'CORS_ALLOWED_ORIGINS': 'https://YOUR_VERCEL_PROJECT.vercel.app',
    'CSRF_TRUSTED_ORIGINS': 'https://YOUR_VERCEL_PROJECT.vercel.app',
    'TIME_ZONE': 'Asia/Kolkata',
    'EMAIL_HOST': 'smtp.gmail.com',
    'EMAIL_PORT': '587',
    'EMAIL_USE_TLS': 'True',
    'EMAIL_HOST_USER': 'your-demo@gmail.com',
    'EMAIL_HOST_PASSWORD': 'paste-the-gmail-app-password-here',
    'DEFAULT_FROM_EMAIL': 'your-demo@gmail.com',
    'SCHEDULER_SECRET': 'paste-a-random-secret-of-at-least-32-characters',
})

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

In the PythonAnywhere web app configuration, add these environment variables. PythonAnywhere’s web UI may require adding them through the WSGI file or account environment-variable settings, depending on the account interface:

```text
DJANGO_SECRET_KEY=<long random value>
DEBUG=False
ALLOWED_HOSTS=YOUR_USERNAME.pythonanywhere.com
CORS_ALLOWED_ORIGINS=https://YOUR_VERCEL_PROJECT.vercel.app
CSRF_TRUSTED_ORIGINS=https://YOUR_VERCEL_PROJECT.vercel.app
TIME_ZONE=Asia/Kolkata
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-demo@gmail.com
EMAIL_HOST_PASSWORD=<16-character Gmail app password>
DEFAULT_FROM_EMAIL=your-demo@gmail.com
SCHEDULER_SECRET=<random value of at least 32 characters>
```

Generate secrets locally with:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Reload the PythonAnywhere web app and test:

```text
https://YOUR_USERNAME.pythonanywhere.com/api/health/
```

Expected response:

```json
{"status":"ok"}
```

SQLite is stored at `backend/db.sqlite3`. Keep this file in the PythonAnywhere project directory; do not use temporary directories.

## 4. Deploy the frontend to Vercel

1. Import the GitHub repository into Vercel.
2. Set the root directory to `frontend/my-react-app`.
3. Set the build command to `npm run build`.
4. Set the output directory to `dist`.
5. Add this environment variable:

```text
VITE_API_URL=https://YOUR_USERNAME.pythonanywhere.com/api
```

Deploy and copy the Vercel URL. Then update PythonAnywhere’s `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS` with the exact Vercel URL and reload the backend.

The SPA rewrite is already configured in `frontend/my-react-app/vercel.json`.

## 5. Configure GitHub Actions

In GitHub repository settings, add these Actions secrets:

```text
BACKEND_CRON_URL=https://YOUR_USERNAME.pythonanywhere.com/api/internal/scheduled-tasks/
SCHEDULER_SECRET=<the exact PythonAnywhere scheduler secret>
```

The workflow at `.github/workflows/scheduled-tasks.yml` sends the secret in the `X-Scheduler-Secret` header. The backend then runs:

```text
finalize_attendance
send_reminders
```

No database, Gmail, or Django secrets are stored in GitHub Actions because the work runs inside PythonAnywhere.

To test manually:

```text
GitHub → repository → Actions → Attendly scheduled tasks → Run workflow
```

## 6. Test the interviewer flow

1. Register a teacher.
2. Verify the teacher through Gmail OTP.
3. Log in as teacher.
4. Create a course.
5. Add a timetable slot for the current day and time.
6. Open an incognito window.
7. Register a student.
8. Verify the student through Gmail OTP.
9. Join the course using the teacher’s join code.
10. Open the attendance code as teacher.
11. Enter the code as student.
12. Check student attendance percentage.
13. Check teacher attendance report.
14. Run the GitHub Actions workflow manually.

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

The free PythonAnywhere account is suitable for this small demonstration but has limited CPU, storage, uptime, and account lifetime. GitHub scheduled jobs may run later than the nominal time.
