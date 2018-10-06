# Generated by Django 2.1.2 on 2018-10-06 07:24

from django.db import migrations, models
import outlook.models.kosmos_errors


class Migration(migrations.Migration):

    dependencies = [
        ('outlook', '0003_auto_20181006_1357'),
    ]

    operations = [
        migrations.CreateModel(
            name='KosmosError',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('olm_filename', models.CharField(db_index=True, default='', max_length=255, verbose_name='olm 文件名')),
                ('olm_item_url', models.CharField(db_index=True, default='', max_length=255, verbose_name='olm 内路径')),
                ('file_obj', models.FileField(null=True, upload_to=outlook.models.kosmos_errors.error_record_path, verbose_name='文件')),
            ],
            options={
                'verbose_name': 'error',
                'verbose_name_plural': 'errors',
            },
        ),
        migrations.AlterUniqueTogether(
            name='kosmoserror',
            unique_together={('olm_filename', 'olm_item_url')},
        ),
    ]
