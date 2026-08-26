from datetime import date
import re
from unittest.mock import patch

from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from .models import Attendance, Course, UserProfile


class AttendanceApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="StrongPass123!")
        self.other_user = User.objects.create_user(username="bob", password="StrongPass123!")
        UserProfile.objects.create(user=self.user, role="student")
        UserProfile.objects.create(user=self.other_user, role="student")
        self.client.force_authenticate(self.user)

    def test_health_endpoint_is_public(self):
        self.client.force_authenticate(None)
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'status': 'ok'})

    @patch("mysite.views.send_email")
    def test_registration_and_login(self, send_email):
        response = self.client.post("/api/register/", {
            "username": "new-user",
            "email": "new@example.com",
            "password": "StrongPass123!",
        })
        self.assertEqual(response.status_code, 202)
        otp = re.search(r"\b\d{6}\b", send_email.call_args.args[1]).group()
        response = self.client.post("/api/register/verify/", {"username": "new-user", "otp": otp})
        self.assertEqual(response.status_code, 201)
        response = self.client.post("/api/token/", {
            "username": "new-user",
            "password": "StrongPass123!",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)

    def test_unauthenticated_api_is_rejected(self):
        self.client.force_authenticate(None)
        response = self.client.get("/api/courses/")
        self.assertEqual(response.status_code, 401)

    def test_user_isolation(self):
        Course.objects.create(user=self.other_user, name="Private", code="PRV")
        response = self.client.get("/api/courses/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_cross_user_course_reference_is_rejected(self):
        course = Course.objects.create(user=self.other_user, name="Private", code="PRV")
        response = self.client.post("/api/attendances/", {
            "course": course.id,
            "date": date.today().isoformat(),
            "is_present": True,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Attendance.objects.count(), 0)

    def test_attendance_summary(self):
        course = Course.objects.create(user=self.user, name="Math", code="MTH")
        Attendance.objects.create(user=self.user, course=course, date=date(2026, 8, 24), is_present=True)
        Attendance.objects.create(user=self.user, course=course, date=date(2026, 8, 25), is_present=False)
        response = self.client.get("/api/attendance-summary/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["attendance_percentage"], 50.0)
        self.assertEqual(response.data["courses"][0]["absent_classes"], 1)

    def test_duplicate_attendance_is_rejected(self):
        course = Course.objects.create(user=self.user, name="Math", code="MTH")
        payload = {"course": course.id, "date": date.today().isoformat(), "is_present": True}
        self.assertEqual(self.client.post("/api/attendances/", payload).status_code, 201)
        self.assertEqual(self.client.post("/api/attendances/", payload).status_code, 400)
