# Attendly API

The complete free deployment guide is in the repository [README.md](../README.md).

## Local setup

```text
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

With `DEBUG=True` and no SMTP credentials, emails are printed to the development console. Production uses Gmail SMTP with a Gmail App Password.

## Scheduled endpoint

GitHub Actions calls this endpoint every 15 minutes:

```text
POST /api/internal/scheduled-tasks/
X-Scheduler-Secret: <configured secret>
```

The endpoint is not authenticated with a user JWT. It requires the shared scheduler secret and runs `finalize_attendance` followed by `send_reminders` inside the PythonAnywhere process.
