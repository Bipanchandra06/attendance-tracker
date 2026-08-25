import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('mysite', '0002_timetableslot_end_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendance',
            name='timetable_slot',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='mysite.timetableslot'),
        ),
        migrations.AlterUniqueTogether(
            name='attendance',
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name='attendance',
            constraint=models.UniqueConstraint(fields=('user', 'timetable_slot', 'date'), name='unique_slot_attendance'),
        ),
        migrations.AddConstraint(
            model_name='attendance',
            constraint=models.UniqueConstraint(condition=models.Q(('timetable_slot__isnull', True)), fields=('user', 'course', 'date'), name='unique_legacy_course_attendance'),
        ),
    ]
