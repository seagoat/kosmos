from django.contrib import admin

from .models import Address, Attachment, Email, KosmosError, Meeting


class EmailAdmin(admin.ModelAdmin):
    # filter_horizontal = ('departments',)
    # list_max_show_all = 5
    readonly_fields = [
        'sender_addresses',
        'bcc_addresses',
        'replyto_addresses',
        'to_addresses',
        'from_addresses',
        'cc_addresses',

    ]
    pass


admin.site.register(Email, EmailAdmin)
admin.site.register(Address)
admin.site.register(Attachment)
admin.site.register(KosmosError)
admin.site.register(Meeting)
