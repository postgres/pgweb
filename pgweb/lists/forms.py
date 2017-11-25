from django import forms

from models import MailingList

class SubscribeForm(forms.Form):
	jquery = True

	email = forms.EmailField(max_length=100,required=True,label="Email address")
	action = forms.ChoiceField(required=True, choices=(('subscribe','Subscribe'),('unsubscribe','Unsubscribe')))
	lists = forms.ModelChoiceField(required=True, queryset=MailingList.objects.filter(active=True), label="Mailinglist")
