from django.contrib import admin
from .models import Attendance, Course, EmailPreference, PendingRegistration, ReminderLog, Timetableslot

admin.site.register(Course)
admin.site.register(Timetableslot)
admin.site.register(Attendance)
admin.site.register((EmailPreference, PendingRegistration, ReminderLog))
