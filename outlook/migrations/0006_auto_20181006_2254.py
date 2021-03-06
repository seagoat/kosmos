# Generated by Django 2.1.2 on 2018-10-06 14:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('outlook', '0005_auto_20181006_1549'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='email',
            name='topic',
        ),
        migrations.AddField(
            model_name='email',
            name='completed_datetime',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='email',
            name='due_datetime',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='email',
            name='has_html',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='email',
            name='html_body',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='email',
            name='mod_date',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='email',
            name='references',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='email',
            name='reminder_datetime',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='email',
            name='sent_time',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='email',
            name='start_datetime',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='email',
            name='thread_index',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='email',
            name='thread_topic',
            field=models.CharField(blank=True, db_index=True, max_length=255, verbose_name='thread_topic'),
        ),
        migrations.AlterField(
            model_name='email',
            name='body',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='email',
            name='message_id',
            field=models.CharField(db_index=True, max_length=255, verbose_name='message_id'),
        ),
        migrations.AlterField(
            model_name='email',
            name='olm_filename',
            field=models.CharField(db_index=True, max_length=255, verbose_name='olm 文件名'),
        ),
        migrations.AlterField(
            model_name='email',
            name='received_time',
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name='email',
            name='subject',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
