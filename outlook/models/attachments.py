from django.db import models


def attachment_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/year/topic/message_id/<filename>
    email = instance.email
    return 'attachment/{year}/{topic}/{message_id}/{filename}'.format(
        year=email.received_time.year,
        topic=email.topic,
        message_id=email.message_id,
        filename=instance.content_name,
    )


class Attachment(models.Model):
    class Meta:
        verbose_name = 'attachment'
        verbose_name_plural = 'attachments'

        # 导出 olm 文件名 + olm 内路径 + message id 应该是唯一
        # 避免重复导入
        unique_together = (
            'olm_filename',
            'content_url',
            'content_name',
            'content_filesize'
        )

    email = models.ForeignKey(
        'Email',
        on_delete=models.CASCADE,
    )

    file_obj = models.FileField(
        verbose_name='文件',
        null=True,
        upload_to=attachment_path
    )

    olm_filename = models.CharField(
        verbose_name='olm 文件名',
        max_length=255,
        default='',
        blank=False,
        db_index=True,
    )

    content_id = models.CharField(
        verbose_name='content_id',
        max_length=255,
        default='',
        blank=False,
        db_index=True,
    )

    content_extension = models.CharField(
        verbose_name='extension',
        max_length=255,
        default='',
        blank=False,
        db_index=True,
    )
    content_name = models.CharField(
        verbose_name='name',
        max_length=255,
        default='',
        blank=False,
        db_index=True,
    )

    content_url = models.CharField(
        verbose_name='url',
        max_length=255,
        default='',
        blank=False,
        db_index=True,
        unique=True,
    )

    content_type = models.CharField(
        verbose_name='type',
        max_length=255,
        default='',
        blank=False,
        db_index=True,
    )

    content_filesize = models.IntegerField(
        verbose_name='filesize',
    )
