from django.db import models


class Category(models.Model):
    class Meta:

        unique_together = ('name', 'color', )

    def __str__(self):
        return '{}[{}]'.format(self.name, self.color)

    name = models.CharField(
        max_length=255,
        blank=False,
        db_index=True,
    )

    color = models.CharField(
        max_length=255,
        blank=False,
        db_index=False,
    )
