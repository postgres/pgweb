from django.contrib import admin
from django.conf import settings

from pgweb.core.models import ModerationNotification
from pgweb.mailqueue.util import send_simple_mail


class PgwebAdmin(admin.ModelAdmin):
    """
    ModelAdmin wrapper that will enable a few pg specific things:
    * Markdown preview for markdown capable textfields (specified by
      including them in a class variable named markdown_capable that is a tuple
      of field names)
    * Add an admin field for "notification", that can be sent to the submitter
      of an item to inform them of moderation issues.
    """

    change_form_template = 'admin/change_form_pgweb.html'

    def formfield_for_dbfield(self, db_field, **kwargs):
        fld = admin.ModelAdmin.formfield_for_dbfield(self, db_field, **kwargs)

        if hasattr(self.model, 'markdown_fields'):
            if db_field.name in self.model.markdown_fields:
                fld.widget.attrs['class'] = fld.widget.attrs['class'] + ' markdown_preview'
        return fld

    def change_view(self, request, object_id, form_url='', extra_context=None):
        if hasattr(self.model, 'send_notification') and self.model.send_notification:
            # Anything that sends notification supports manual notifications
            if extra_context == None:
                extra_context = dict()
            extra_context['notifications'] = ModerationNotification.objects.filter(objecttype=self.model.__name__, objectid=object_id).order_by('date')

        return super(PgwebAdmin, self).change_view(request, object_id, form_url, extra_context)

    # Remove the builtin delete_selected action, so it doesn't
    # conflict with the custom one.
    def get_actions(self, request):
        actions = super(PgwebAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions

    # Define a custom delete_selected action. This is required because the
    # default one uses the delete functionality in QuerySet, which bypasses
    # the delete() operation on the model, and thus won't send out our
    # notifications. Manually calling delete() on each one will be slightly
    # slower, but will send proper notifications - and it's not like this
    # is something that happens often enough that we care about performance.
    def custom_delete_selected(self, request, queryset):
        for x in queryset:
            x.delete()
    custom_delete_selected.short_description = "Delete selected items"
    actions=['custom_delete_selected']

    def save_model(self, request, obj, form, change):
        if change and hasattr(self.model, 'send_notification') and self.model.send_notification:
            # We only do processing if something changed, not when adding
            # a new object.
            if request.POST.has_key('new_notification') and request.POST['new_notification']:
                # Need to send off a new notification. We'll also store
                # it in the database for future reference, of course.
                if not obj.org.email:
                    # Should not happen because we remove the form field. Thus
                    # a hard exception is ok.
                    raise Exception("Organisation does not have an email, canot send notification!")
                n = ModerationNotification()
                n.objecttype = obj.__class__.__name__
                n.objectid = obj.id
                n.text = request.POST['new_notification']
                n.author = request.user.username
                n.save()

                # Now send an email too
                msgstr = _get_notification_text(obj,
                                                request.POST['new_notification'])

                send_simple_mail(settings.NOTIFICATION_FROM,
                                 obj.org.email,
                                 "postgresql.org moderation notification",
                                 msgstr)

                # Also generate a mail to the moderators
                send_simple_mail(settings.NOTIFICATION_FROM,
                                 settings.NOTIFICATION_EMAIL,
                                 "Moderation comment on %s %s" % (obj.__class__._meta.verbose_name, obj.id),
                                 _get_moderator_notification_text(obj,
                                                                  request.POST['new_notification'],
                                                                  request.user.username
                                                              ))


        # Either no notifications, or done with notifications
        super(PgwebAdmin, self).save_model(request, obj, form, change)


def register_pgwebadmin(model):
    admin.site.register(model, PgwebAdmin)


def _get_notification_text(obj, txt):
    objtype = obj.__class__._meta.verbose_name
    return """You recently submitted a %s to postgresql.org.

During moderation, this item has received comments that need to be
addressed before it can be approved. The comment given by the moderator is:

%s

Please go to https://www.postgresql.org/account/ and make any changes
request, and your submission will be re-moderated.
""" % (objtype, txt)



def _get_moderator_notification_text(obj, txt, moderator):
    return """Moderator %s made a comment to a pending object:
Object type: %s
Object id: %s
Comment: %s
""" % (moderator,
       obj.__class__._meta.verbose_name,
       obj.id,
       txt,
       )
