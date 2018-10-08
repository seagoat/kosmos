import os

from django.db import models


class Olm(models.Model):
    class Meta:
        # unique_together = ('filename', 'filesize', 'hash_value')
        pass

    def __str__(self):
        return '{}'.format(self.filename)

    @property
    def filename(self):
        return os.path.basename(self.olm_filename)

    olm_filename = models.CharField(
        max_length=255,
        blank=False,
        db_index=True,
    )

    filesize = models.IntegerField(

    )

    hash_value = models.CharField(
        max_length=255,
        blank=False,
        db_index=True,
    )
