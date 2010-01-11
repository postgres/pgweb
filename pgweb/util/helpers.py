from django.shortcuts import render_to_response, get_object_or_404
from pgweb.util.contexts import NavContext
from django.http import HttpResponseRedirect
from django.template import Context
from django.template.loader import get_template

def simple_form(instancetype, itemid, request, formclass, formtemplate='base/form.html', redirect='/account/', navsection='account'):
	if itemid == 'new':
		instance = instancetype()
	else:
		# Regular news item, attempt to edit it
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
	}, NavContext(request, navsection))

def template_to_string(templatename, attrs = {}):
	return get_template(templatename).render(Context(attrs))

def add_xml_element(xml, name, value):
	xml.startElement(name, {})
	xml.characters(value)
	xml.endElement(name)
