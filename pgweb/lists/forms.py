from django import forms

from models import MailingList

class SubscribeForm(forms.Form):
	email = forms.EmailField(max_length=100,required=True,label="Email address")
	action = forms.ChoiceField(required=True, choices=(('subscribe','Subscribe'),('unsubscribe','Unsubscribe')))
	receive = forms.BooleanField(required=False, label="Receive mail", initial=True)
	digest = forms.BooleanField(required=False, label="Digest only")
	lists = forms.ModelChoiceField(required=True, queryset=MailingList.objects.filter(active=True), label="Mailinglist")

