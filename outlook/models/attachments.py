from celery.utils.log import get_task_logger
from django.db import models

log = get_task_logger(__name__)


def attachment_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/year/topic/message_id/<filename>
    email = instance.email
    return 'attachment/{year}/{topic}/{message_id}/{filename}'.format(
        year=email.sent_time.year,
        topic=email.thread_topic,
        message_id=email.message_id,
        filename=instance.content_name,
    )
    # return 'attachment/{olm_filename}/{filename}'.format(
    #     olm_filename=instance.olm_filename,
    #     filename=instance.content_name,
    # )


class Attachment(models.Model):
    class Meta:
        # 导出 olm 文件名 + olm 内路径 + message id 应该是唯一
        # 避免重复导入
        unique_together = (
            'olm_filename',
            'olm_item_url',
            'email',
        )

    def __str__(self):
        return self.content_name

    email = models.ForeignKey(
        'Email',
        on_delete=models.CASCADE,
    )

    file_obj = models.FileField(
        verbose_name='文件',
        null=True,
        upload_to=attachment_path,
        max_length=1024,
    )

    olm_filename = models.CharField(
        max_length=255,
        blank=False,
        db_index=True,
    )

    olm_item_url = models.CharField(
        max_length=255,
        blank=False,
        db_index=True,
    )

    content_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    content_extension = models.CharField(
        max_length=255,
        blank=True,
        default='',
        null=True,
    )
    content_name = models.CharField(
        max_length=255,
        blank=True,
        default='',
        null=True,
    )

    content_type = models.CharField(
        max_length=255,
        blank=True,
        default='',
        null=True,
    )

    content_filesize = models.IntegerField(
        null=True,
    )
