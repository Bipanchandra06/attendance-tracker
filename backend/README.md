# Attendly API

## Run locally

```text
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

For full deployment instructions, see the repository [README.md](../README.md). Never commit `.env` or any Gmail credentials.

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

Run the reminder command from a scheduler or GitHub Actions:

```text
python manage.py send_reminders
```

After 07:10 it sends that day's timetable once. It also sends a reminder when an hour-starting class has passed its first 10 minutes and attendance has not been recorded. Reminder emails use Gmail API in production, respect each user's opt-out setting, and are logged to prevent duplicates.
