import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Attendance, Course, EmailPreference, PendingRegistration, Timetableslot
from .serializers import (AccountSerializer, Attendanceserializer, Courseserializer,
                          PasswordSerializer, RegistrationSerializer,
                          Timetableserializer, VerifyRegistrationSerializer)

class CourseView(viewsets.ModelViewSet):
    queryset=Course.objects.none()
    def get_queryset(self):
        return Course.objects.filter(user=self.request.user)
    serializer_class=Courseserializer
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TimetableView(viewsets.ModelViewSet):
    queryset=Timetableslot.objects.none()
    def get_queryset(self):
        queryset = Timetableslot.objects.filter(user=self.request.user).select_related("course")
        day = self.request.query_params.get("day")
        return queryset.filter(day=day) if day else queryset.order_by("day", "time")
    serializer_class=Timetableserializer
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AttendanceView(viewsets.ModelViewSet):
    queryset=Attendance.objects.none()
    def get_queryset(self):
        queryset = Attendance.objects.filter(user=self.request.user).select_related("course")
        for field in ("course", "date"):
            value = self.request.query_params.get(field)
            if value:
                queryset = queryset.filter(**{field: value})
        start = self.request.query_params.get("from_date")
        end = self.request.query_params.get("to_date")
        if start:
            queryset = queryset.filter(date__gte=start)
        if end:
            queryset = queryset.filter(date__lte=end)
        return queryset.order_by("-date")
    serializer_class=Attendanceserializer
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    serializer = RegistrationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    if User.objects.filter(email=data["email"]).exists():
        return Response({"email": ["An account with this email already exists."]}, status=400)
    otp = f"{secrets.randbelow(1000000):06d}"
    PendingRegistration.objects.filter(username=data["username"]).delete()
    PendingRegistration.objects.create(
        username=data["username"], email=data["email"], password_hash=make_password(data["password"]),
        otp_hash=make_password(otp), expires_at=timezone.now() + timedelta(minutes=10),
    )
    send_mail("Your Attendly verification code", f"Your verification code is {otp}. It expires in 10 minutes.", settings.DEFAULT_FROM_EMAIL, [data["email"]])
    return Response({"detail": "Verification code sent.", "username": data["username"]}, status=status.HTTP_202_ACCEPTED)


@api_view(["POST"])
@permission_classes([AllowAny])
def verify_registration(request):
    serializer = VerifyRegistrationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        pending = PendingRegistration.objects.get(username=serializer.validated_data["username"])
    except PendingRegistration.DoesNotExist:
        return Response({"detail": "Registration expired or not found."}, status=400)
    if pending.expires_at <= timezone.now():
        pending.delete()
        return Response({"detail": "Verification code expired."}, status=400)
    if pending.attempts >= 5:
        pending.delete()
        return Response({"detail": "Too many attempts. Please register again."}, status=429)
    pending.attempts += 1
    pending.save(update_fields=["attempts"])
    from django.contrib.auth.hashers import check_password
    if not check_password(serializer.validated_data["otp"], pending.otp_hash):
        return Response({"otp": ["Invalid verification code."]}, status=400)
    with transaction.atomic():
        user = User.objects.create(username=pending.username, email=pending.email, password=pending.password_hash)
        EmailPreference.objects.create(user=user)
        pending.delete()
    return Response({"id": user.id, "username": user.username, "email": user.email}, status=201)


@api_view(["GET", "PATCH"])
def account(request):
    preference, _ = EmailPreference.objects.get_or_create(user=request.user)
    if request.method == "PATCH":
        serializer = AccountSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
    return Response(AccountSerializer(request.user).data)


@api_view(["POST"])
def change_password(request):
    serializer = PasswordSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    request.user.set_password(serializer.validated_data["new_password"])
    request.user.save(update_fields=["password"])
    return Response({"detail": "Password updated."})


@api_view(["GET"])
def attendance_summary(request):
    courses = Course.objects.filter(user=request.user).annotate(
        total_classes=Count("attendance"),
        present_classes=Count("attendance", filter=Q(attendance__is_present=True)),
    )
    summary = []
    for course in courses:
        total = course.total_classes
        present = course.present_classes
        summary.append({
            "course_id": course.id,
            "course_name": course.name,
            "course_code": course.code,
            "total_classes": total,
            "present_classes": present,
            "absent_classes": total - present,
            "attendance_percentage": round((present / total) * 100, 2) if total else 0,
        })
    total = sum(item["total_classes"] for item in summary)
    present = sum(item["present_classes"] for item in summary)
    return Response({
        "courses": summary,
        "total_classes": total,
        "present_classes": present,
        "absent_classes": total - present,
        "attendance_percentage": round((present / total) * 100, 2) if total else 0,
    })

