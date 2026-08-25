from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone

from mysite.models import Attendance, EmailPreference, ReminderLog, Timetableslot


class Command(BaseCommand):
    help = 'Send morning schedule and late attendance reminder emails.'

    def handle(self, *args, **options):
        now = timezone.localtime()
        today = now.date()
        if now.minute != 10:
            self.stdout.write('No reminder run: command is scheduled for :10 each hour.')
            return
        slots = Timetableslot.objects.select_related('user', 'course').filter(day=now.strftime('%A'))
        sent = 0
        for user in {slot.user for slot in slots}:
            preference, _ = EmailPreference.objects.get_or_create(user=user)
            if not preference.reminders_enabled or not user.email:
                continue
            user_slots = [slot for slot in slots if slot.user_id == user.id]
            if now.hour == 7 and not ReminderLog.objects.filter(user=user, date=today, kind='morning').exists():
                schedule = '\n'.join(f'{slot.time.strftime("%H:%M")} - {slot.end_time.strftime("%H:%M") if slot.end_time else "?"}: {slot.course.name} ({slot.course.code})' for slot in user_slots)
                send_mail("Today's class schedule", f"Good morning!\n\nToday's schedule:\n{schedule or 'No classes scheduled.'}", None, [user.email])
                ReminderLog.objects.create(user=user, timetable_slot=user_slots[0], date=today, kind='morning')
                sent += 1
            for slot in user_slots:
                start = timezone.make_aware(datetime.combine(today, slot.time))
                if slot.time.minute != 0 or slot.time.hour != now.hour or now < start + timedelta(minutes=10):
                    continue
                if Attendance.objects.filter(user=user, timetable_slot=slot, date=today).exists():
                    continue
                if ReminderLog.objects.filter(user=user, timetable_slot=slot, date=today, kind='late').exists():
                    continue
                send_mail(f'Attendance reminder: {slot.course.name}', f'Your {slot.course.name} class started at {slot.time.strftime("%H:%M")}. Please record your attendance.', None, [user.email])
                ReminderLog.objects.create(user=user, timetable_slot=slot, date=today, kind='late')
                sent += 1
        self.stdout.write(self.style.SUCCESS(f'Sent {sent} reminder email(s).'))
