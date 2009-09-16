def ssl_required(fn):
	def _require_ssl(request, *_args, **_kwargs):
		return fn(request, *_args, **_kwargs)
	return _require_ssl
