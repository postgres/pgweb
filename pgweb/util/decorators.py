def ssl_required(fn):
	def _require_ssl(*_args):
		return fn(_args)
	return _require_ssl
