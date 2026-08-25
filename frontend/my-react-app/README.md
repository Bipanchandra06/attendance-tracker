# Attendly frontend

React/Vite client for the attendance tracker.

## Run locally

```text
npm install
npm run dev
```

The app expects Django at `http://localhost:8000`. Set `VITE_API_URL` when the backend uses another URL, for example `VITE_API_URL=http://localhost:8000/api`.

## Available workflows

- Register and sign in with JWT
- Manage courses
- Manage timetable slots
- Record present or absent attendance
- View attendance totals and percentages

The access and refresh tokens are stored under the `attendance_tokens` local-storage key and are removed on sign out.
