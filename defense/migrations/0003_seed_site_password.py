from django.db import migrations


def create_password(apps, schema_editor):
    SitePassword = apps.get_model('defense', 'SitePassword')
    if not SitePassword.objects.filter(id=1).exists():
        SitePassword.objects.create(id=1, password='aimssn')


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('defense', '0002_student_started_by_session_alter_session_name'),
    ]

    operations = [
        migrations.RunPython(create_password, reverse_func),
    ]
