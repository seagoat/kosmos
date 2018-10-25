import os

from django.db import models


class Olm(models.Model):
    class Meta:
        unique_together = ('filename', 'filesize', 'hash_value')
        pass

    def __str__(self):
        return '{}|{}'.format(self.filename, self.olm_filename)

    def save(self, *args, **kwargs):
        print('olm_filename:[{}], filenaem:[{}]'.format(
            self.olm_filename, self.filename))
        self.filename = os.path.basename(self.olm_filename)
        print('olm_filename:[{}], filenaem:[{}]'.format(
            self.olm_filename, self.filename))
        super().save(*args, **kwargs)

    filename = models.CharField(
        max_length=255,
        blank=False,
        db_index=True,
    )

    olm_filename = models.CharField(
        max_length=255,
        blank=False,
        db_index=True,
        null=False,
    )

    filesize = models.IntegerField(
        null=False,
    )

    hash_value = models.CharField(
        max_length=255,
        blank=False,
        db_index=True,
        null=False,
    )

    finished = models.BooleanField(
        default=False,
    )
