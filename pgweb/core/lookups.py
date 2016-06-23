from django.contrib.auth.models import User
from selectable.base import ModelLookup
from selectable.registry import registry
from selectable.decorators import staff_member_required


@staff_member_required
class UserLookup(ModelLookup):
	model = User
	search_fields = (
		'username__icontains',
		'first_name__icontains',
		'last_name__icontains',
	)
	filters = {'is_active': True, }

	def get_item_value(self, item):
		# Display for currently selected item
		return u"%s (%s)" % (item.username, item.get_full_name())

	def get_item_label(self, item):
		# Display for choice listings
		return u"%s (%s)" % (item.username, item.get_full_name())

registry.register(UserLookup)
