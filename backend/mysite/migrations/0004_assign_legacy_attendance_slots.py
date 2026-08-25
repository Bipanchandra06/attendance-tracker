from django.db import migrations


def assign_legacy_slots(apps, schema_editor):
    Attendance = apps.get_model('mysite', 'Attendance')
    Timetableslot = apps.get_model('mysite', 'Timetableslot')
    for record in Attendance.objects.filter(timetable_slot__isnull=True):
        day = record.date.strftime('%A')
        slot = Timetableslot.objects.filter(
            user_id=record.user_id,
            course_id=record.course_id,
            day=day,
        ).order_by('time').first()
        if slot:
            record.timetable_slot_id = slot.id
            record.save(update_fields=['timetable_slot'])


class Migration(migrations.Migration):
    dependencies = [
        ('mysite', '0003_attendance_timetable_slot'),
    ]

    operations = [
        migrations.RunPython(assign_legacy_slots, migrations.RunPython.noop),
    ]
