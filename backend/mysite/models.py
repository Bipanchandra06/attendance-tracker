from django.db import models
from django.contrib.auth.models import User
import secrets

class Course(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    teacher=models.ForeignKey(User,on_delete=models.CASCADE,related_name="taught_courses",null=True,blank=True)
    name=models.CharField(max_length=100)
    code=models.CharField(max_length=10)
    join_code=models.CharField(max_length=20,unique=True,null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name+"-"+self.code

class Timetableslot(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    day=models.CharField(max_length=10)
    time=models.TimeField()
    end_time=models.TimeField(null=True, blank=True)
    course=models.ForeignKey(Course, on_delete=models.CASCADE)
    def __str__(self):
        return self.course.name+"-"+self.course.code
    class Meta:
        unique_together = ("user", "day", "time")
 
class Attendance(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)   
    course=models.ForeignKey(Course, on_delete=models.CASCADE)
    timetable_slot=models.ForeignKey(Timetableslot, on_delete=models.CASCADE, null=True, blank=True)
    attendance_session=models.ForeignKey("AttendanceSession", on_delete=models.CASCADE, null=True, blank=True)
    marked_at=models.DateTimeField(auto_now_add=True, null=True)
    date=models.DateField()
    is_present=models.BooleanField(default=False)
    # Geofence student location fields
    student_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    student_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("user", "timetable_slot", "date"), name="unique_slot_attendance"),
            models.UniqueConstraint(fields=("user", "course", "date"), condition=models.Q(timetable_slot__isnull=True), name="unique_legacy_course_attendance"),
        ]


class PendingRegistration(models.Model):
    role = models.CharField(max_length=20, default="student")
    username = models.CharField(max_length=150)
    email = models.EmailField()
    password_hash = models.CharField(max_length=128)
    otp_hash = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)


class EmailPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="email_preference")
    reminders_enabled = models.BooleanField(default=True)


class ReminderLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timetable_slot = models.ForeignKey(Timetableslot, on_delete=models.CASCADE)
    date = models.DateField()
    kind = models.CharField(max_length=20)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("user", "timetable_slot", "date", "kind"), name="unique_reminder_log"),
        ]


class UserProfile(models.Model):
    ROLE_CHOICES = (("student", "Student"), ("teacher", "Teacher"))
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="student")


class CourseEnrollment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="course_enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("student", "course"), name="unique_student_course_enrollment")]


class AttendanceSession(models.Model):
    timetable_slot = models.ForeignKey(Timetableslot, on_delete=models.CASCADE, related_name="attendance_sessions")
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name="attendance_sessions")
    session_date = models.DateField()
    code_hash = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    is_open = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # Geofence fields
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    radius_meters = models.IntegerField(default=100, null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("timetable_slot", "session_date"), condition=models.Q(is_open=True), name="unique_open_slot_session_date")]


class DeviceFingerprint(models.Model):
    """
    Lightweight device tracking to prevent multi-account abuse on the same device.
    Stores a hashed device ID per user and session to detect suspicious patterns.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="device_fingerprints")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="device_fingerprints")
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name="device_fingerprints", null=True, blank=True)
    device_hash = models.CharField(max_length=128)  # Hashed device fingerprint
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("user", "course", "session"), name="unique_device_per_user_session"),
        ]