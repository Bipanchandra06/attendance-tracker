# Attendly API

## Run locally

```text
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Before starting the server, edit `.env` and replace the placeholder Gmail address and App Password. Use a Gmail App Password, not the normal Gmail password. Never commit `.env`.

The API runs at `http://localhost:8000` and accepts the Vite frontend at `http://localhost:5173`.

## Authentication

- `POST /api/register/` with `username`, `email`, and `password`
- `POST /api/token/` with `username` and `password`
- `POST /api/token/refresh/` with a refresh token

Send the access token as `Authorization: Bearer <token>` for protected endpoints.

## Resources

- `/api/courses/`
- `/api/timetables/` with optional `?day=Monday`
- `/api/attendances/` with optional course/date filters
- `/api/attendance-summary/`

All resource queries are restricted to the authenticated user. Run the test suite with `python manage.py test`.

## Email features

- `POST /api/register/` sends a six-digit OTP and keeps the registration pending for 10 minutes.
- `POST /api/register/verify/` verifies the OTP and creates the account.
- `GET/PATCH /api/account/` reads or updates email and reminder preferences.
- `POST /api/account/password/` changes the password.

Run the reminder command hourly at 10 minutes past the hour with Windows Task Scheduler or another scheduler:

```text
python manage.py send_reminders
```

At 07:10 it sends that day's timetable. At every other `:10` run, it sends a reminder for an hour-starting class if attendance has not been recorded in its first 10 minutes. Reminder emails respect each user's opt-out setting and are logged to prevent duplicates. The command exits without sending if started at another minute.
