from django.db import models
from django.contrib.auth.models import User

class Course(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    name=models.CharField(max_length=100)
    code=models.CharField(max_length=10)
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
    date=models.DateField()
    is_present=models.BooleanField(default=False)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("user", "timetable_slot", "date"), name="unique_slot_attendance"),
            models.UniqueConstraint(fields=("user", "course", "date"), condition=models.Q(timetable_slot__isnull=True), name="unique_legacy_course_attendance"),
        ]


class PendingRegistration(models.Model):
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