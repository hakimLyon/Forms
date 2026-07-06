from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('defense', '0010_evaluation_edit_token'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='supervisor_2_institution',
            field=models.CharField(blank=True, default='', max_length=200),
            preserve_default=False,
        ),
    ]
