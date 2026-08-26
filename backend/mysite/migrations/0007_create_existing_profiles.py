from django.db import migrations


def create_profiles(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    UserProfile = apps.get_model('mysite', 'UserProfile')
    Course = apps.get_model('mysite', 'Course')
    teacher_ids = set(Course.objects.filter(teacher__isnull=False).values_list('teacher_id', flat=True))
    for user in User.objects.all():
        UserProfile.objects.get_or_create(user_id=user.id, defaults={'role': 'teacher' if user.id in teacher_ids else 'student'})


class Migration(migrations.Migration):
    dependencies = [('mysite', '0006_attendance_marked_at_course_created_at_and_more')]
    operations = [migrations.RunPython(create_profiles, migrations.RunPython.noop)]
