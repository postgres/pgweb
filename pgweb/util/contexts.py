from django.template import RequestContext
from django.conf import settings

# This is the whole site navigation structure. Stick in a smarter file?
sitenav = {
	'about': [
		{'title': 'About',              'link':'/about/'},
		{'title': 'Advantages',         'link':'/about/advantages/'},
		{'title': 'Feature Matrix',     'link':'/about/featurematrix/'},
		{'title': 'Awards',             'link':'/about/awards/'},
		{'title': 'Donate',             'link':'/about/donate/'},
		{'title': 'Case Studies',       'link':'/about/casestudies/'},
		{'title': 'Quotes',             'link':'/about/quotesarchive/'},
		{'title': 'Featured Users',     'link':'/about/users/'},
		{'title': 'History',            'link':'/about/history/'},
		{'title': 'Sponsors',           'link':'/about/sponsors/', 'submenu': [
			{'title': 'Servers',    'link': '/about/servers/'},
		]},
		{'title': 'Latest news',        'link':'/about/newsarchive/'},
		{'title': 'Upcoming events',    'link':'/about/eventarchive/'},
		{'title': 'Press',              'link':'/about/press/'},
		{'title': 'Licence',            'link':'/about/licence/'},
	],
	'download': [
		{'title': 'Downloads',          'link':'/download/', 'submenu': [
				{'title': 'Binary',		'link':'/download/'},
				{'title': 'Source',		'link':'/ftp/source/'}
		]},
		{'title': 'Software Catalogue', 'link':'/download/product-categories/'},
		{'title': 'pgFoundry',          'link':'http://pgfoundry.org/'},
		{'title': 'File Browser',       'link':'/ftp/'},
	],
	'docs': [
		{'title': 'Documentation',      'link':'/docs/'},
		{'title': 'Manuals',            'link':'/docs/manuals/', 'submenu': [
			{'title': 'Archive',    'link':'/docs/manuals/archive/'},
			{'title': 'French',     'link':'http://docs.postgresqlfr.org/'},
			{'title': 'Japanese',   'link':'http://www.postgresql.jp/document/'},
		]},
		{'title': 'Security',           'link':'/support/security/'},
		{'title': 'What\'s New',        'link':'/docs/9.2/static/release-9-2-2.html'},
		{'title': 'FAQ',                'link':'http://wiki.postgresql.org/wiki/Category:FAQ'},
		{'title': 'Books',              'link':'/docs/books/'},
		{'title': 'Wiki',               'link':'http://wiki.postgresql.org'},
	],
	'community': [
		{'title': 'Community',          'link':'/community/'},
		{'title': 'Contributors',       'link':'/community/contributors/'},
		{'title': 'Mailing Lists',      'link':'/community/lists/', 'submenu': [
			{'title': 'Subscribe',  'link':'/community/lists/subscribe/'},
			{'title': 'Archives',   'link':'http://archives.postgresql.org/'},
		]},
		{'title': 'IRC',                'link':'/community/irc/'},
		{'title': 'Featured Users',     'link':'/about/users/'},
		{'title': 'International Sites','link':'/community/international/'},
		{'title': 'Propaganda',         'link':'/community/propaganda/'},
		{'title': 'Resources',          'link':'/community/resources/'},
		{'title': 'Weekly News',        'link':'/community/weeklynews/'},
	],
	'developer': [
		{'title': 'Developers',         'link':'/developer/'},
		{'title': 'Roadmap',            'link':'/developer/roadmap/'},
		{'title': 'Coding',             'link':'/developer/coding/'},
		{'title': 'Testing',            'link':'/developer/testing/', 'submenu': [
			{'title': 'Alpha Information', 'link':'/developer/alpha/'},
			{'title': 'Beta Information',  'link':'/developer/beta/'},
		]},
		{'title': 'Mailing Lists',      'link':'/community/lists/'},
		{'title': 'Developer FAQ',      'link':'http://wiki.postgresql.org/wiki/Developer_FAQ'},
	],
	'support': [
		{'title': 'Support',            'link':'/support/'},
		{'title': 'Versioning policy',  'link':'/support/versioning/'},
		{'title': 'Security',           'link':'/support/security/'},
		{'title': 'Professional Services','link':'/support/professional_support/'},
		{'title': 'Hosting Solutions',  'link':'/support/professional_hosting/'},
		{'title': 'Report a Bug',       'link':'/support/submitbug/'},
	],
	'account': [
		{'title': 'Your account',         'link':'/account'},
		{'title': 'Profile',            'link':'/account/profile'},
		{'title': 'Submitted data',          'link':'/account', 'submenu': [
			{'title': 'News Articles',  'link':'/account/edit/news/'},
			{'title': 'Events',         'link':'/account/edit/events/'},
			{'title': 'Products',       'link':'/account/edit/products/'},
			{'title': 'Professional Services', 'link':'/account/edit/services/'},
			{'title': 'Organisations',  'link':'/account/edit/organisations/'},
		]},
		{'title': 'Change password',    'link':'/account/changepwd/'},
		{'title': 'Logout',             'link':'/account/logout'},
	],
}


class NavContext(RequestContext):
	def __init__(self, request, section):
		RequestContext.__init__(self, request)
		if sitenav.has_key(section):
			navsection = sitenav[section]
		else:
			navsection = {}
		self.update({'navmenu': navsection})


# Template context processor to add information about the root link
def RootLinkContextProcessor(request):
	if request.is_secure():
		return {
			'link_root': settings.SITE_ROOT,
		}
	else:
		return {}

