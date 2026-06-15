from django.db import migrations


def create_pvsettings(apps, schema_editor):
    PVSettings = apps.get_model('defense', 'PVSettings')
    if not PVSettings.objects.filter(id=1).exists():
        PVSettings.objects.create(
            id=1,
            director_name='Dr. Coura Balde',
            director_title='Academic Manager, AIMS Senegal',
            institution_name='AIMS Senegal',
        )


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('defense', '0004_pvsettings'),
    ]

    operations = [
        migrations.RunPython(create_pvsettings, reverse_func),
    ]
