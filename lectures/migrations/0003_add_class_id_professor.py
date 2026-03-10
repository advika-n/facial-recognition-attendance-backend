from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lectures', '0002_teacher'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='class_id',
            field=models.CharField(default='', max_length=50),
        ),
        migrations.AddField(
            model_name='course',
            name='professor_id',
            field=models.CharField(blank=True, default='', max_length=30),
        ),
    ]
