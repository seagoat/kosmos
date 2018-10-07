import os

from django.db import models


def meeting_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/olm_file_path/olm_item_url
    return 'meeting/{olm_filename}/{olm_item_url}'.format(
        olm_filename=instance.olm_filename.replace('..', ''),
        olm_item_url=os.path.basename(instance.olm_item_url),
    )


class Meeting(models.Model):
    class Meta:
        # 导出 olm 文件名 + olm 内路径 + message id 应该是唯一
        # 避免重复导入
        unique_together = (
            'olm_filename',
            'olm_item_url',
        )

    def __str__(self):
        return self.olm_item_url

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

    file_obj = models.FileField(
        verbose_name='文件',
        null=True,
        upload_to=meeting_path
    )
