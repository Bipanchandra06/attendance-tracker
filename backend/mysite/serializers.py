from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.password_validation import validate_password
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError
from mysite.models import (Attendance, AttendanceSession, Course, CourseEnrollment,
                            EmailPreference, Timetableslot)
from rest_framework import serializers


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ("username", "email", "password")

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class VerifyRegistrationSerializer(serializers.Serializer):
    username = serializers.CharField()
    otp = serializers.CharField(min_length=6, max_length=6)


class AccountSerializer(serializers.ModelSerializer):
    reminders_enabled = serializers.BooleanField(source="email_preference.reminders_enabled", required=False)
    role = serializers.CharField(source="profile.role", read_only=True)

    class Meta:
        model = User
        fields = ("username", "email", "role", "reminders_enabled")
        read_only_fields = ("username",)

    def update(self, instance, validated_data):
        preference_data = validated_data.pop("email_preference", {})
        instance.email = validated_data.get("email", instance.email)
        instance.save(update_fields=["email"])
        if "reminders_enabled" in preference_data:
            preference, _ = EmailPreference.objects.get_or_create(user=instance)
            preference.reminders_enabled = preference_data["reminders_enabled"]
            preference.save(update_fields=["reminders_enabled"])
        return instance


class PasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])

    def validate_current_password(self, password):
        if not check_password(password, self.context["request"].user.password):
            raise serializers.ValidationError("Current password is incorrect.")
        return password

class Timetableserializer(serializers.ModelSerializer):
    class Meta:
        model = Timetableslot
        fields = ("id", "day", "time", "end_time", "course", "user")
        read_only_fields = ("user",)

    def validate_day(self, day):
        if day not in {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}:
            raise serializers.ValidationError("Day must be a valid weekday.")
        return day

    def validate(self, attrs):
        if attrs.get("end_time") and attrs["end_time"] <= attrs.get("time", self.instance.time if self.instance else attrs["end_time"]):
            raise serializers.ValidationError("End time must be after start time.")
        user = self.context["request"].user
        if Timetableslot.objects.filter(user=user, day=attrs.get("day"), time=attrs.get("time")).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise serializers.ValidationError("A timetable slot already exists at this day and time.")
        return attrs

    def validate_course(self, course):
        if course.user_id != self.context["request"].user.id:
            raise serializers.ValidationError("You can only use your own courses.")
        return course

class Courseserializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ("id", "name", "code", "teacher", "join_code", "created_at", "user")
        read_only_fields = ("user", "teacher", "join_code", "created_at")
    
class Attendanceserializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = ("id", "course", "timetable_slot", "attendance_session", "date", "is_present", "user", "marked_at", "student_latitude", "student_longitude")
        read_only_fields = ("user", "marked_at")

    def validate_course(self, course):
        if course.user_id != self.context["request"].user.id:
            raise serializers.ValidationError("You can only use your own courses.")
        return course

    def validate_timetable_slot(self, slot):
        if slot is None:
            return slot
        if slot.user_id != self.context["request"].user.id:
            raise serializers.ValidationError("You can only use your own timetable slots.")
        return slot

    def validate(self, attrs):
        user = self.context["request"].user
        slot = attrs.get("timetable_slot")
        query = {"user": user, "date": attrs.get("date")}
        query["timetable_slot" if slot else "course"] = slot if slot else attrs.get("course")
        if Attendance.objects.filter(**query).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise serializers.ValidationError("Attendance has already been recorded for this slot and date.")
        return attrs


class JoinCourseSerializer(serializers.Serializer):
    join_code = serializers.CharField(max_length=20)


class AttendanceCodeSerializer(serializers.Serializer):
    code = serializers.RegexField(regex=r"^\d{6}$", error_messages={"invalid": "Attendance code must be six digits."})


class GeofencedAttendanceSerializer(serializers.Serializer):
    """Serializer for geofenced attendance marking by students."""
    session_id = serializers.IntegerField()
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    device_fingerprint = serializers.CharField(max_length=256)  # Client-side generated device ID


class AttendanceSessionSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source="timetable_slot.course.name", read_only=True)
    course_code = serializers.CharField(source="timetable_slot.course.code", read_only=True)
    slot_time = serializers.TimeField(source="timetable_slot.time", read_only=True)
    code = serializers.SerializerMethodField()

    def get_code(self, obj):
        # The raw attendance code is only attached by the create-session view.
        return None

    class Meta:
        model = AttendanceSession
        fields = ("id", "timetable_slot", "session_date", "expires_at", "is_open", "course_name", "course_code", "slot_time", "code", "latitude", "longitude", "radius_meters")
        read_only_fields = ("id", "session_date", "expires_at", "is_open", "course_name", "course_code", "slot_time", "code", "created_at")





