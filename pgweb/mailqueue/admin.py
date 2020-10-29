from django.contrib import admin

from email.parser import Parser
from email import policy

from .models import QueuedMail


class QueuedMailAdmin(admin.ModelAdmin):
    model = QueuedMail
    readonly_fields = ('parsed_content', )
    list_display = ('pk', 'sender', 'receiver', 'sendat')

    def parsed_content(self, obj):
        # We only try to parse the *first* piece, because we assume
        # all our emails are trivial.
        try:
            parser = Parser(policy=policy.default)
            msg = parser.parsestr(obj.fullmsg)
            return msg.get_body(preferencelist=('plain', )).get_payload(decode=True).decode('utf8')
        except Exception as e:
            return "Failed to get body: %s" % e

    parsed_content.short_description = 'Parsed mail'


admin.site.register(QueuedMail, QueuedMailAdmin)
