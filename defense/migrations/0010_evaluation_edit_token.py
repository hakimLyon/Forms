import secrets

from django.db import migrations, models


def backfill_edit_tokens(apps, schema_editor):
    Evaluation = apps.get_model('defense', 'Evaluation')
    for ev in Evaluation.objects.filter(edit_token=''):
        ev.edit_token = secrets.token_urlsafe(24)
        ev.save(update_fields=['edit_token'])


class Migration(migrations.Migration):

    dependencies = [
        ('defense', '0009_student_id_student'),
    ]

    operations = [
        migrations.AddField(
            model_name='evaluation',
            name='edit_token',
            field=models.CharField(blank=True, default='', max_length=64),
        ),
        migrations.RunPython(backfill_edit_tokens, migrations.RunPython.noop),
    ]
