# Generated by Django 2.1.2 on 2018-10-06 16:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('outlook', '0009_auto_20181006_2352'),
    ]

    operations = [
        migrations.AlterField(
            model_name='email',
            name='mentioned_me',
            field=models.BooleanField(null=True),
        ),
        migrations.AlterField(
            model_name='email',
            name='override_encoding',
            field=models.BooleanField(null=True),
        ),
    ]
