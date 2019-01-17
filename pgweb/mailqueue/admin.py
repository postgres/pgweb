from django.contrib import admin

from email.parser import Parser

from models import QueuedMail


class QueuedMailAdmin(admin.ModelAdmin):
    model = QueuedMail
    readonly_fields = ('parsed_content', )

    def parsed_content(self, obj):
        # We only try to parse the *first* piece, because we assume
        # all our emails are trivial.
        try:
            parser = Parser()
            msg = parser.parsestr(obj.fullmsg)
            b = msg.get_payload(decode=True)
            if b: return b

            pl = msg.get_payload()
            for p in pl:
                b = p.get_payload(decode=True)
                if b: return b
            return "Could not find body"
        except Exception, e:
            return "Failed to get body: %s" % e

    parsed_content.short_description = 'Parsed mail'


admin.site.register(QueuedMail, QueuedMailAdmin)
