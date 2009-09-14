from django.shortcuts import render_to_response, get_object_or_404
from pgweb.util.contexts import NavContext
from django.http import HttpResponseRedirect

def simple_form(instancetype, itemid, request, formclass, formtemplate='base/form.html', redirect='/account/', navsection='account'):
	if itemid == 'new':
		instance = instancetype()
	else:
		# Regular news item, attempt to edit it
		instance = get_object_or_404(instancetype, pk=itemid)
		if not instance.submitter == request.user:
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

	return render_to_response(formtemplate, {
		'form': form,
		'formitemtype': instance._meta.verbose_name,
	}, NavContext(request, navsection))

