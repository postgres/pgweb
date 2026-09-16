from django import forms
from django.forms import ValidationError
from django.conf import settings

from pgweb.core.models import Organisation
from .models import Contributor, Badge, Badgeholder
from django.contrib.auth.models import User

from pgweb.util.middleware import get_current_user
from pgweb.mailqueue.util import send_simple_mail

from datetime import date


class ContributorModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        contributor = Contributor.objects.filter(user=obj.pk)
        if contributor:
            return f"{obj.first_name} {obj.last_name} ({obj.username}) <{obj.email}>"
        else:
            return f"{obj.first_name} {obj.last_name} ({obj.username}) <{obj.email}> (not a contributor yet)"


class BadgeForm(forms.ModelForm):
    form_intro = 'Contributor badges acknowledge people contributing time to the PostgreSQL project and the ecosystem around it. If you manage an organisation that gives people the opportunity to contribute (like volunteering or speaking at a conference, writing code for an extension, translating messages, helping others use PostgreSQL, organise the community, ...), you can issue a badge to acknowledge these contributions.'

    add_holder = forms.CharField(required=False, help_text="Enter email addresses of postgresql.org user accounts to award the badge to. Separate multiple addresses with whitespace.")
    retire_holder = ContributorModelMultipleChoiceField(required=False, queryset=None, label="Current badge holders", help_text="Select one or more users to retire.")
    remove_holder = ContributorModelMultipleChoiceField(required=False, queryset=None, label="Retired badge holders", help_text="Select one or more users to remove. To un-retire a user, add their email address again in the first field.")

    fieldsets = [
        {
            'id': 'general',
            'legend': 'Contributor Badge',
            'fields': ['org', 'badge', 'description', 'url', 'imagedata', 'contact', ],
        },
        {
            'id': 'holders',
            'legend': 'Badge Holders',
            'fields': ['add_holder', 'retire_holder', 'remove_holder'],
        },
    ]

    class Meta:
        model = Badge
        exclude = ('approved', 'sortorder', 'holders', 'slug',)

    def __init__(self, *args, **kwargs):
        super(BadgeForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['retire_holder'].queryset = self.instance.holders.filter(badgeholder__date_retired__isnull=True)
            self.fields['remove_holder'].queryset = self.instance.holders.filter(badgeholder__date_retired__isnull=False)
        else:
            del self.fields['add_holder']
            del self.fields['retire_holder']
            del self.fields['remove_holder']
            # remove the holders fieldset
            self.fieldsets = [fs for fs in self.fieldsets if fs['id'] != 'holders']

    def clean_add_holder(self):
        if self.cleaned_data['add_holder']:
            for u in self.cleaned_data['add_holder'].split():
                # something was added - let's make sure the user exists
                try:
                    User.objects.get(email=u.lower())
                except User.DoesNotExist:
                    raise ValidationError("User with email %s not found" % u)

        return self.cleaned_data['add_holder']

    def save(self, commit=True):
        badge = super(BadgeForm, self).save(commit=False)

        ops = []

        if 'add_holder' in self.cleaned_data and self.cleaned_data['add_holder']:
            for u in self.cleaned_data['add_holder'].split():
                user = User.objects.get(email=u.lower())
                holder = Badgeholder.objects.get_or_create(user=user, badge=badge, defaults={'awarded_by': get_current_user()})[0]
                if holder.date_retired:  # un-retire them
                    holder.date_retired = None
                    holder.save()
                    ops.append('Un-retired badge holder {}'.format(user.username))
                else:
                    ops.append('Added badge holder {}'.format(user.username))
        if 'retire_holder' in self.cleaned_data and self.cleaned_data['retire_holder']:
            for toretire in self.cleaned_data['retire_holder']:
                holder = Badgeholder.objects.get(badge=badge, user=toretire)
                holder.date_retired = date.today()
                holder.save()
                ops.append('Retired badge holder {}'.format(toretire.username))
        if 'remove_holder' in self.cleaned_data and self.cleaned_data['remove_holder']:
            for toremove in self.cleaned_data['remove_holder']:
                badge.holders.remove(toremove)
                ops.append('Removed badge holder {}'.format(toremove.username))

        if ops:
            send_simple_mail(
                settings.NOTIFICATION_FROM,
                settings.NOTIFICATION_EMAIL,
                "{0} modified {1}".format(get_current_user().username, badge),
                "The following changes were made to {}:\n\n{}".format(badge, "\n".join(ops))
            )

        return badge

    def filter_by_user(self, user):
        self.fields['org'].queryset = Organisation.objects.filter(managers=user, approved=True)
