from django.shortcuts import render_to_response, get_object_or_404
from pgweb.util.contexts import NavContext
from django.http import HttpResponseRedirect, Http404
from django.template import Context
from django.template.loader import get_template
import django.utils.xmlutils

def simple_form(instancetype, itemid, request, formclass, formtemplate='base/form.html', redirect='/account/', navsection='account', fixedfields=None, createifempty=False):
	if itemid == 'new':
		instance = instancetype()
	else:
		# Regular form item, attempt to edit it
		try:
			i = int(itemid)
		except ValueError:
			raise Http404("Invalid URL")
		if createifempty:
			(instance, wascreated) = instancetype.objects.get_or_create(pk=itemid)
		else:
			instance = get_object_or_404(instancetype, pk=itemid)
		if hasattr(instance, 'submitter'):
			if not instance.submitter == request.user:
				raise Exception("You are not the owner of this item!")
		elif hasattr(instance, 'verify_submitter'):
			if not instance.verify_submitter(request.user):
				raise Exception("You are not the owner of this item!")
	
	if request.method == 'POST':
		# Process this form
		form = formclass(data=request.POST, instance=instance)
		if form.is_valid():
			r = form.save(commit=False)
			r.submitter = request.user
			# Set fixed fields. Note that this will not work if the fixed fields are ManyToMany,
			# but we'll fix that sometime in the future
			if fixedfields:
				for k,v in fixedfields.items():
					setattr(r, k, v)
			r.save()

			# If we have a callback with the current user
			if hasattr(form, 'apply_submitter'):
				form.apply_submitter(r, request.user)
				r.save()

			return HttpResponseRedirect(redirect)
	else:
		# Generate form
		form = formclass(instance=instance)

	if hasattr(form, 'filter_by_user'):
		form.filter_by_user(request.user)

	if hasattr(instancetype, 'markdown_fields'):
		markdownfields = instancetype.markdown_fields
	else:
		markdownfields = None

	return render_to_response(formtemplate, {
		'form': form,
		'formitemtype': instance._meta.verbose_name,
		'markdownfields': markdownfields,
		'form_intro': hasattr(form, 'form_intro') and form.form_intro or None,
		'toggle_fields': hasattr(form, 'toggle_fields') and form.toggle_fields or None,
		'jquery': hasattr(form, 'jquery') and form.jquery or None,
		'savebutton': (itemid == "new") and "New" or "Save",
		'operation': (itemid == "new") and "New" or "Edit",
	}, NavContext(request, navsection))

def template_to_string(templatename, attrs = {}):
	return get_template(templatename).render(Context(attrs))

def HttpServerError(msg):
	r = render_to_response('errors/500.html', {
			'message': msg,
			})
	r.status_code = 500
	return r


class PgXmlHelper(django.utils.xmlutils.SimplerXMLGenerator):
	def __init__(self, outstream, skipempty=False):
		django.utils.xmlutils.SimplerXMLGenerator.__init__(self, outstream, 'utf-8')
		self.skipempty = skipempty

	def add_xml_element(self, name, value):
		if self.skipempty and value=='': return
		self.startElement(name, {})
		self.characters(value)
		self.endElement(name)

