# Generated by Django 2.1.2 on 2018-10-07 07:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('outlook', '0028_auto_20181007_1530'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attachment',
            name='email',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='outlook.Email'),
        ),
    ]
