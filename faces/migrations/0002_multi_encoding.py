from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('faces', '0001_initial'),
        ('students', '0001_initial'),
    ]

    operations = [
        # Step 1: add label column
        migrations.AddField(
            model_name='faceencoding',
            name='label',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
        # Step 2: drop the old unique constraint that came with OneToOneField,
        #         then change to ForeignKey (many-to-one)
        migrations.AlterField(
            model_name='faceencoding',
            name='student',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='face_encodings',
                to='students.student',
            ),
        ),
    ]
