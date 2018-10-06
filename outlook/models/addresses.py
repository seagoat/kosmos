from django.db import models


class Address(models.Model):
    class Meta:
        verbose_name = 'address'
        verbose_name_plural = 'addresses'
        unique_together = ('address', 'name', 'content_type')

    def __str__(self):
        return '{}[{}]'.format(self.name, self.address)

    address = models.CharField(
        verbose_name='address',
        max_length=255,
        default='',
        blank=False,
        db_index=True,
    )

    name = models.CharField(
        verbose_name='name',
        max_length=255,
        default='',
        blank=True,
        db_index=True,
    )

    content_type = models.CharField(
        verbose_name='type',
        max_length=255,
        default='',
        blank=True,
        db_index=True,
    )
