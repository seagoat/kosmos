from django.db import models


class Email(models.Model):
    class Meta:
        verbose_name = 'email'
        verbose_name_plural = 'emails'

        # 导出 olm 文件名 + olm 内路径 + message id 应该是唯一
        # 避免重复导入
        unique_together = ('olm_filename', 'olm_item_url', 'message_id')

    def __str__(self):
        return self.subject

    olm_filename = models.CharField(
        verbose_name='olm 文件名',
        max_length=255,
        default='',
        blank=False,
        db_index=True,
    )

    olm_item_url = models.CharField(
        verbose_name='olm 内路径',
        max_length=255,
        default='',
        blank=False,
        db_index=True,
    )

    message_id = models.CharField(
        verbose_name='message_id',
        max_length=255,
        default='',
        blank=False,
        db_index=True,
    )

    topic = models.CharField(
        verbose_name='topic',
        max_length=255,
        default='',
        blank=True,
        null=True,
        db_index=True,
    )

    received_time = models.DateTimeField(
        verbose_name='received_time',
        null=True,
    )

    subject = models.CharField(
        verbose_name='subject',
        max_length=255,
        default='',
        blank=True,
        db_index=True,
        null=True,
    )

    body = models.TextField(
        verbose_name='body',
        default='',
        blank=True,
        null=True,
    )
