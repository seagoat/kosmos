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
        blank=False,
        db_index=True,
    )

    thread_topic = models.CharField(
        verbose_name='thread_topic',
        max_length=255,
        blank=True,
        db_index=True,
    )

    subject = models.CharField(
        max_length=255,
        blank=True,
    )

    thread_index = models.CharField(
        max_length=255,
        blank=True,
    )

    received_time = models.DateTimeField(
        null=True,
    )

    sent_time = models.DateTimeField(
        null=True,
    )

    completed_datetime = models.DateTimeField(
        null=True,
    )

    due_datetime = models.DateTimeField(
        null=True,
    )

    start_datetime = models.DateTimeField(
        null=True,
    )

    mod_date = models.DateTimeField(
        null=True,
    )

    reminder_datetime = models.DateTimeField(
        null=True,
    )

    has_html = models.BooleanField(
        null=True,
    )

    body = models.TextField(
        blank=True,
    )

    html_body = models.TextField(
        blank=True,
    )

    references = models.CharField(
        max_length=255,
        blank=True,
    )

    replyto = models.CharField(
        max_length=255,
        blank=True,
    )

    receive_representing_name = models.CharField(
        max_length=255,
        blank=True,
    )

    calendar_accept_status = models.CharField(
        max_length=255,
        blank=True,
    )

    send_read_receipt = models.CharField(
        max_length=255,
        blank=True,
    )

    mentioned_me = models.BooleanField(
        null=True
    )

    inference_classfication = models.CharField(
        max_length=255,
        blank=True,
    )

    has_richtext = models.BooleanField(
        null=True,
    )

    is_read = models.BooleanField(
        null=True,
    )

    override_encoding = models.BooleanField(
        null=True,
    )

    priority = models.CharField(
        max_length=255,
        blank=True,
    )

    source = models.CharField(
        max_length=255,
        blank=True,
    )

    flag_status = models.CharField(
        max_length=255,
        blank=True,
    )

    was_sent = models.BooleanField(
        null=True,
    )

    calendar_message = models.CharField(
        max_length=255,
        blank=True,
    )

    is_meeting = models.BooleanField(
        null=True,
    )

    is_outgoing = models.BooleanField(
        null=True,
    )

    is_outgoing_meeting_respoonse = models.BooleanField(
        null=True,
    )

    bcc_addresses = models.ManyToManyField(
        'Address',
        related_name='bcc_addresses+',
    )

    replyto_addresses = models.ManyToManyField(
        'Address',
        related_name='replyto_addresses+',
    )

    to_addresses = models.ManyToManyField(
        'Address',
        related_name='to_addresses+',
    )

    from_addresses = models.ManyToManyField(
        'Address',
        related_name='from_addresses+',
    )

    cc_addresses = models.ManyToManyField(
        'Address',
        related_name='cc_addresses+',
    )
