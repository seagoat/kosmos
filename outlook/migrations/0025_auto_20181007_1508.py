# Generated by Django 2.1.2 on 2018-10-07 07:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('outlook', '0024_auto_20181007_1425'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='attachment',
            unique_together={('olm_filename', 'content_url')},
        ),
    ]
