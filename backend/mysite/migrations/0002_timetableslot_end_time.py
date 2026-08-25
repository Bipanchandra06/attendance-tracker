from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('mysite', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='timetableslot',
            name='end_time',
            field=models.TimeField(blank=True, null=True),
        ),
    ]
