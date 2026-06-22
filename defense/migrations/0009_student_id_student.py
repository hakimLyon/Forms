from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('defense', '0008_evaluation_score_analysis_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='id_student',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
    ]
