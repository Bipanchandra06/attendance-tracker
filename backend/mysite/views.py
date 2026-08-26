import hashlib
import hmac
import io
import secrets
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
from django.core.management import call_command
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from .models import (Attendance, AttendanceSession, Course, CourseEnrollment,
                     EmailPreference, PendingRegistration, Timetableslot,
                     UserProfile)
from .email_service import send_email
from .serializers import (AccountSerializer, Attendanceserializer, Courseserializer,
                          AttendanceCodeSerializer, AttendanceSessionSerializer,
                          JoinCourseSerializer, PasswordSerializer,
                          RegistrationSerializer, Timetableserializer,
                          VerifyRegistrationSerializer)


def role(request, expected):
    return (
        request.user.is_authenticated
        and hasattr(request.user, "profile")
        and request.user.profile.role.strip().lower() == expected.lower()
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    return Response({"status": "ok"})


@api_view(["POST"])
@permission_classes([AllowAny])
def run_scheduled_tasks(request):
    provided = request.headers.get('X-Scheduler-Secret', '')
    if not settings.SCHEDULER_SECRET or not hmac.compare_digest(provided, settings.SCHEDULER_SECRET):
        return Response({"detail": "Unauthorized scheduler request."}, status=status.HTTP_401_UNAUTHORIZED)

    finalize_output = io.StringIO()
    reminders_output = io.StringIO()
    call_command('finalize_attendance', stdout=finalize_output)
    call_command('send_reminders', stdout=reminders_output)
    return Response({
        "status": "ok",
        "finalize_attendance": finalize_output.getvalue().strip(),
        "send_reminders": reminders_output.getvalue().strip(),
    })

class CourseView(viewsets.ModelViewSet):
    queryset=Course.objects.none()
    def get_queryset(self):
        if role(self.request, "teacher"):
            return Course.objects.filter(teacher=self.request.user)
        return Course.objects.filter(enrollments__student=self.request.user, enrollments__is_active=True)
    serializer_class=Courseserializer
    def perform_create(self, serializer):
        if not role(self.request, "teacher"):
            raise PermissionDenied("Only teachers can create courses.")
        serializer.save(user=self.request.user, teacher=self.request.user)


class TimetableView(viewsets.ModelViewSet):
    queryset=Timetableslot.objects.none()
    def get_queryset(self):
        queryset = Timetableslot.objects.filter(user=self.request.user).select_related("course")
        day = self.request.query_params.get("day")
        return queryset.filter(day=day) if day else queryset.order_by("day", "time")
    serializer_class=Timetableserializer
    def perform_create(self, serializer):
        if not role(self.request, "teacher"):
            raise PermissionDenied("Only teachers can create timetable slots.")
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
        if not role(self.request, "student"):
            raise PermissionDenied("Use an attendance session code to mark attendance.")
        serializer.save(user=self.request.user)


def create_pending_registration(request, registration_role):
    serializer = RegistrationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    if User.objects.filter(email=data["email"]).exists():
        return Response({"email": ["An account with this email already exists."]}, status=400)
    otp = f"{secrets.randbelow(1000000):06d}"
    PendingRegistration.objects.filter(username=data["username"]).delete()
    PendingRegistration.objects.create(
        role=registration_role,
        username=data["username"], email=data["email"], password_hash=make_password(data["password"]),
        otp_hash=make_password(otp), expires_at=timezone.now() + timedelta(minutes=10),
    )
    send_email("Your Attendly verification code", f"Your verification code is {otp}. It expires in 10 minutes.", [data["email"]])
    return Response({"detail": "Verification code sent.", "username": data["username"]}, status=status.HTTP_202_ACCEPTED)


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    return create_pending_registration(request, "student")


@api_view(["POST"])
@permission_classes([AllowAny])
def register_teacher(request):
    return create_pending_registration(request, "teacher")


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
        UserProfile.objects.create(user=user, role=pending.role)
        pending.delete()
    return Response({"id": user.id, "username": user.username, "email": user.email}, status=201)


@api_view(["GET", "PATCH"])
def account(request):
    preference, _ = EmailPreference.objects.get_or_create(user=request.user)
    profile, _ = UserProfile.objects.get_or_create(user=request.user, defaults={"role": "student"})
    if request.method == "PATCH":
        serializer = AccountSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
    data = AccountSerializer(request.user).data
    data["role"] = profile.role.strip().lower()
    return Response(data)


@api_view(["POST"])
def change_password(request):
    serializer = PasswordSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    request.user.set_password(serializer.validated_data["new_password"])
    request.user.save(update_fields=["password"])
    return Response({"detail": "Password updated."})


@api_view(["GET"])
def attendance_summary(request):
    courses = Course.objects.filter(
        Q(enrollments__student=request.user, enrollments__is_active=True) | Q(user=request.user)
    ).distinct() if role(request, "student") else Course.objects.filter(teacher=request.user)
    attendance_filter = Q(attendance__user=request.user) if role(request, "student") else Q()
    courses = courses.annotate(
        total_classes=Count("attendance", filter=attendance_filter),
        present_classes=Count("attendance", filter=attendance_filter & Q(attendance__is_present=True)),
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


def teacher_course(course, user):
    return course.teacher_id == user.id or (course.teacher_id is None and course.user_id == user.id)


@api_view(["GET", "POST"])
def teacher_courses(request):
    if not role(request, "teacher"):
        return Response({"detail": "Teacher access required."}, status=403)
    if request.method == "POST":
        serializer = Courseserializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = f"{serializer.validated_data['code'].upper()}-{secrets.token_urlsafe(5).upper()[:5]}"
        course = Course.objects.create(user=request.user, teacher=request.user, join_code=code, name=serializer.validated_data["name"], code=serializer.validated_data["code"])
        return Response(Courseserializer(course).data, status=201)
    result = []
    for course in Course.objects.filter(teacher=request.user):
        data = Courseserializer(course).data
        data["enrollment_count"] = course.enrollments.filter(is_active=True).count()
        data["timetableslots"] = Timetableserializer(Timetableslot.objects.filter(course=course).order_by("day", "time"), many=True).data
        result.append(data)
    return Response(result)


@api_view(["POST"])
def regenerate_join_code(request, course_id):
    if not role(request, "teacher"):
        return Response({"detail": "Teacher access required."}, status=403)
    course = Course.objects.filter(id=course_id, teacher=request.user).first()
    if not course:
        return Response({"detail": "Course not found."}, status=404)
    course.join_code = f"{course.code.upper()}-{secrets.token_urlsafe(5).upper()[:5]}"
    course.save(update_fields=["join_code"])
    return Response({"join_code": course.join_code})


@api_view(["POST"])
def join_course(request):
    if not role(request, "student"):
        return Response({"detail": "Student access required."}, status=403)
    serializer = JoinCourseSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    course = Course.objects.filter(join_code=serializer.validated_data["join_code"].strip().upper()).first()
    if not course:
        return Response({"join_code": ["Invalid course code."]}, status=400)
    enrollment, created = CourseEnrollment.objects.get_or_create(student=request.user, course=course, defaults={"is_active": True})
    if not created and enrollment.is_active:
        return Response({"detail": "You already joined this course."}, status=400)
    enrollment.is_active = True
    enrollment.save(update_fields=["is_active"])
    return Response(Courseserializer(course).data, status=201)


@api_view(["GET"])
def student_courses(request):
    if not role(request, "student"):
        return Response({"detail": "Student access required."}, status=403)
    courses = Course.objects.filter(enrollments__student=request.user, enrollments__is_active=True)
    return Response(Courseserializer(courses, many=True).data)


@api_view(["GET"])
def student_timetable(request):
    if not role(request, "student"):
        return Response({"detail": "Student access required."}, status=403)
    return Response(Timetableserializer(Timetableslot.objects.filter(course__enrollments__student=request.user, course__enrollments__is_active=True).order_by("day", "time"), many=True).data)


@api_view(["POST"])
def teacher_slot(request, course_id):
    if not role(request, "teacher"):
        return Response({"detail": "Teacher access required."}, status=403)
    course = Course.objects.filter(id=course_id, teacher=request.user).first()
    if not course:
        return Response({"detail": "Course not found."}, status=404)
    serializer = Timetableserializer(data={**request.data, "course": course.id}, context={"request": request})
    serializer.is_valid(raise_exception=True)
    slot = serializer.save(user=request.user)
    return Response(Timetableserializer(slot).data, status=201)


@api_view(["POST"])
def create_attendance_session(request, slot_id):
    if not role(request, "teacher"):
        return Response({"detail": "Teacher access required."}, status=403)
    slot = Timetableslot.objects.filter(id=slot_id, course__teacher=request.user).select_related("course").first()
    if not slot:
        return Response({"detail": "Slot not found."}, status=404)
    today = timezone.localdate()
    now = timezone.localtime()
    if slot.day != now.strftime("%A"):
        return Response({"detail": "Attendance codes can only be generated on the scheduled day."}, status=400)
    start = timezone.make_aware(datetime.combine(today, slot.time))
    fallback_end = (datetime.combine(today, slot.time) + timedelta(hours=1)).time()
    end = timezone.make_aware(datetime.combine(today, slot.end_time or fallback_end))
    if not start <= now <= end:
        return Response({"detail": "Attendance codes can only be generated during the class time."}, status=400)
    AttendanceSession.objects.filter(
        timetable_slot=slot, session_date=today, is_open=True, expires_at__lte=timezone.now()
    ).update(is_open=False)
    if AttendanceSession.objects.filter(timetable_slot=slot, session_date=today, is_open=True).exists():
        return Response({"detail": "An attendance session is already open."}, status=400)
    code = f"{secrets.randbelow(1000000):06d}"
    session = AttendanceSession.objects.create(timetable_slot=slot, teacher=request.user, session_date=today, code_hash=make_password(code), expires_at=timezone.now() + timedelta(minutes=2))
    data = AttendanceSessionSerializer(session).data
    data["code"] = code
    return Response(data, status=201)


@api_view(["POST"])
def close_attendance_session(request, session_id):
    if not role(request, "teacher"):
        return Response({"detail": "Teacher access required."}, status=403)
    session = AttendanceSession.objects.filter(id=session_id, teacher=request.user).first()
    if not session:
        return Response({"detail": "Session not found."}, status=404)
    session.is_open = False
    session.save(update_fields=["is_open"])
    return Response({"detail": "Session closed."})


@api_view(["POST"])
def mark_session_attendance(request):
    if not role(request, "student"):
        return Response({"detail": "Student access required."}, status=403)
    serializer = AttendanceCodeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    sessions = AttendanceSession.objects.filter(is_open=True, expires_at__gt=timezone.now()).select_related("timetable_slot__course")
    session = next((item for item in sessions if check_password(serializer.validated_data["code"], item.code_hash)), None)
    if not session or not CourseEnrollment.objects.filter(student=request.user, course=session.timetable_slot.course, is_active=True).exists():
        return Response({"code": ["Invalid, expired, or unauthorized attendance code."]}, status=400)
    attendance, created = Attendance.objects.get_or_create(user=request.user, course=session.timetable_slot.course, timetable_slot=session.timetable_slot, attendance_session=session, date=session.session_date, defaults={"is_present": True})
    if not created:
        return Response({"detail": "Attendance already marked."}, status=400)
    return Response({"course_name": session.timetable_slot.course.name, "course_code": session.timetable_slot.course.code, "date": session.session_date, "is_present": True, "slot_time": session.timetable_slot.time}, status=201)


@api_view(["GET"])
def teacher_attendance_report(request, course_id):
    if not role(request, "teacher"):
        return Response({"detail": "Teacher access required."}, status=403)
    course = Course.objects.filter(id=course_id, teacher=request.user).first()
    if not course:
        return Response({"detail": "Course not found."}, status=404)
    rows = []
    for enrollment in CourseEnrollment.objects.filter(course=course, is_active=True).select_related("student"):
        records = Attendance.objects.filter(user=enrollment.student, course=course).order_by("date")
        total = records.count()
        present = records.filter(is_present=True).count()
        rows.append({"student_id": enrollment.student_id, "student_username": enrollment.student.username, "student_email": enrollment.student.email, "total_classes": total, "present_classes": present, "absent_classes": total - present, "attendance_percentage": round(present * 100 / total, 2) if total else 0, "attendance_by_date": [{"date": record.date, "status": "present" if record.is_present else "absent"} for record in records]})
    return Response(rows)

