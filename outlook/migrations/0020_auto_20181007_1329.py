# Generated by Django 2.1.2 on 2018-10-07 05:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('outlook', '0019_auto_20181007_1326'),
    ]

    operations = [
        migrations.AlterField(
            model_name='email',
            name='thread_index',
            field=models.TextField(blank=True),
        ),
    ]
