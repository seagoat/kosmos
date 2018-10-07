# Generated by Django 2.1.2 on 2018-10-07 06:25

from django.db import migrations, models
import django.db.models.deletion
import outlook.models.meetings


class Migration(migrations.Migration):

    dependencies = [
        ('outlook', '0023_auto_20181007_1403'),
    ]

    operations = [
        migrations.CreateModel(
            name='Meeting',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('olm_filename', models.CharField(db_index=True, default='', max_length=255, verbose_name='olm 文件名')),
                ('olm_item_url', models.CharField(db_index=True, default='', max_length=255, verbose_name='olm 内路径')),
                ('file_obj', models.FileField(null=True, upload_to=outlook.models.meetings.meeting_path, verbose_name='文件')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='meeting',
            unique_together={('olm_filename', 'olm_item_url')},
        ),
        migrations.AddField(
            model_name='email',
            name='meeting_data',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='outlook.Meeting'),
        ),
    ]
