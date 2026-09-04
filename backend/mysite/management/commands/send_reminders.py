from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone

from mysite.models import Attendance, CourseEnrollment, EmailPreference, ReminderLog, Timetableslot
from mysite.email_service import send_email


class Command(BaseCommand):
    help = 'Send morning schedule and late attendance reminder emails.'

    def handle(self, *args, **options):
        now = timezone.localtime()
        today = now.date()
        slots = list(Timetableslot.objects.select_related('course').filter(day=now.strftime('%A')).order_by('time'))
        sent = 0
        student_ids = CourseEnrollment.objects.filter(
            course_id__in={slot.course_id for slot in slots}, is_active=True
        ).values_list('student_id', flat=True).distinct()
        for user_id in student_ids:
            user = User.objects.get(id=user_id)
            preference, _ = EmailPreference.objects.get_or_create(user=user)
            if not preference.reminders_enabled or not user.email:
                continue
            enrolled_course_ids = set(CourseEnrollment.objects.filter(
                student=user, is_active=True
            ).values_list('course_id', flat=True))
            user_slots = [slot for slot in slots if slot.course_id in enrolled_course_ids]
            if not user_slots:
                continue
            # GitHub Actions/PythonAnywhere can run late, so send the morning
            # message any time after 07:10 if it has not already been sent.
            morning_due = now.hour > 7 or (now.hour == 7 and now.minute >= 10)
            if morning_due and not ReminderLog.objects.filter(user=user, date=today, kind='morning').exists():
                schedule = '\n'.join(f'{slot.time.strftime("%H:%M")} - {slot.end_time.strftime("%H:%M") if slot.end_time else "?"}: {slot.course.name} ({slot.course.code})' for slot in user_slots)
                send_email("Today's class schedule", f"Good morning!\n\nToday's schedule:\n{schedule or 'No classes scheduled.'}", [user.email])
                ReminderLog.objects.create(user=user, timetable_slot=user_slots[0], date=today, kind='morning')
                sent += 1
            for slot in user_slots:
                start = timezone.make_aware(datetime.combine(today, slot.time))
                # Do not require classes to start exactly on the hour. The
                # scheduler may run every 15 minutes and timetable times can
                # be any minute.
                if now < start + timedelta(minutes=10):
                    continue
                if Attendance.objects.filter(user=user, timetable_slot=slot, date=today).exists():
                    continue
                if ReminderLog.objects.filter(user=user, timetable_slot=slot, date=today, kind='late').exists():
                    continue
                send_email(f'Attendance reminder: {slot.course.name}', f'Your {slot.course.name} class started at {slot.time.strftime("%H:%M")}. Please record your attendance.', [user.email])
                ReminderLog.objects.create(user=user, timetable_slot=slot, date=today, kind='late')
                sent += 1
        self.stdout.write(self.style.SUCCESS(f'Sent {sent} reminder email(s).'))
