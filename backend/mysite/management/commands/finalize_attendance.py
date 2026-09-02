from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from mysite.models import Attendance, AttendanceSession, CourseEnrollment


class Command(BaseCommand):
    help = 'Create absent attendance records for students after class ends.'

    def handle(self, *args, **options):
        now = timezone.localtime()
        created = 0
        sessions = AttendanceSession.objects.filter(is_open=True, session_date__lte=now.date()).select_related('timetable_slot', 'timetable_slot__course')
        for session in sessions:
            end_time = session.timetable_slot.end_time or (datetime.combine(session.session_date, session.timetable_slot.time) + timedelta(hours=1)).time()
            class_end = timezone.make_aware(datetime.combine(session.session_date, end_time))
            if now < class_end:
                continue
            students = CourseEnrollment.objects.filter(course=session.timetable_slot.course, is_active=True).values_list('student_id', flat=True)
            for student_id in students:
                # Attendance is unique per student, timetable slot, and date.
                # A student may already have checked in through another session,
                # so do not use a session-specific get_or_create lookup here.
                existing = Attendance.objects.filter(
                    user_id=student_id,
                    timetable_slot=session.timetable_slot,
                    date=session.session_date,
                ).exists()
                if not existing:
                    Attendance.objects.create(
                        user_id=student_id, course=session.timetable_slot.course,
                        timetable_slot=session.timetable_slot, attendance_session=session,
                        date=session.session_date, is_present=False,
                    )
                    created += 1
            session.is_open = False
            session.save(update_fields=['is_open'])
        self.stdout.write(self.style.SUCCESS(f'Created {created} absent attendance record(s).'))
