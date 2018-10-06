from django.contrib import admin

from .models import Address, Attachment, Email

# Register your models here.
admin.site.register(Email)
admin.site.register(Address)
admin.site.register(Attachment)
