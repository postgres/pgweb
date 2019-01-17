from django.contrib import admin
from django import forms

from pgweb.util.admin import PgwebAdmin
from models import Event

def approve_event(modeladmin, request, queryset):
    # We need to do this in a loop even though it's less efficient,
    # since using queryset.update() will not send the moderation messages.
    for e in queryset:
        e.approved = True
        e.save()
approve_event.short_description = 'Approve event'

class EventAdminForm(forms.ModelForm):
    class Meta:
        model = Event
        exclude = ()

    def clean(self):
        cleaned_data = super(EventAdminForm, self).clean()
        if not cleaned_data.get('isonline'):
            if not cleaned_data.get('city'):
                self._errors['city'] = self.error_class(['City must be specified for non-online events'])
                del cleaned_data['city']
            if not cleaned_data.get('country'):
                self._errors['country'] = self.error_class(['Country must be specified for non-online events'])
                del cleaned_data['country']
        return cleaned_data

class EventAdmin(PgwebAdmin):
    list_display = ('title', 'org', 'startdate', 'enddate', 'approved',)
    list_filter = ('approved',)
    search_fields = ('summary', 'details', 'title', )
    actions = [approve_event, ]
    form = EventAdminForm


admin.site.register(Event, EventAdmin)
