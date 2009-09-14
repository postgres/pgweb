// Functions to generate showdown previews for
// the django admin interface

var converter = null;

function attach_showdown_preview(objid) {
	if (!converter) {
		converter = new Showdown.converter();
	}
	obj = document.getElementById(objid);

	if (!obj) {
	   alert('Could not locate object ' + objid + ' in DOM');
	   return;
	}
	obj.style.cssFloat = 'left';
	obj.style.marginRight = '10px';
	newdiv = document.createElement('div');
	newdiv.className = 'markdownpreview';
	obj.style.width = newdiv.style.width = "400px";
	obj.style.height = newdiv.style.height = "200px";

	obj.parentNode.insertBefore(newdiv, obj.nextSibling);

	update_markdown(obj, newdiv);

	window.onkeyup = obj.onkeyup = function() {
		/* Using a timer make sure we only update max 4 times / second */
		if (obj.current_timeout) {
			clearTimeout(obj.current_timeout);
		}
		obj.current_timeout = setTimeout(function() {
			update_markdown(obj, newdiv);
		}, 250);
	};
}

function update_markdown(src, dest) {
	if (src.value != src.lastvalue) {
		src.lastvalue = src.value;
		dest.innerHTML = converter.makeHtml(src.value);
	}
}
