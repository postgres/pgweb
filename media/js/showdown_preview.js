// Functions to generate showdown previews for
// the django admin interface

var converter = null;

function attach_showdown_preview(objid, admin) {
	if (!converter) {
		converter = new Showdown.converter();
	}
	obj = document.getElementById(objid);

	if (!obj) {
	   alert('Could not locate object ' + objid + ' in DOM');
	   return;
	}

	newdiv = document.createElement('div');
	newdiv.className = 'markdownpreview';

	if (admin) {
		obj.style.cssFloat = 'left';
		obj.style.marginRight = '10px';
		obj.style.width = newdiv.style.width = "400px";
		obj.style.height = newdiv.style.height = "200px";
	}

	obj.preview_div = newdiv;

	obj.parentNode.insertBefore(newdiv, obj.nextSibling);

	if (!admin) {
	   infospan = document.createElement('span');
	   infospan.innerHTML = 'This field supports markdown. See below for a preview.';
	   obj.parentNode.insertBefore(infospan, newdiv);
	}

	update_markdown(obj, newdiv);

	window.onkeyup = function() {
		/* Using a timer make sure we only update max 4 times / second */
		if (obj.current_timeout) {
			clearTimeout(obj.current_timeout);
		}
		obj.current_timeout = setTimeout(function() {
			e = document.getElementsByTagName('textarea');
			for (i= 0; i < e.length; i++) {
				if (e[i].preview_div) {
					update_markdown(e[i], e[i].preview_div);
				}
			}
		}, 250);
	};
}

function update_markdown(src, dest) {
	if (src.value != src.lastvalue) {
		src.lastvalue = src.value;
		dest.innerHTML = converter.makeHtml(src.value);
	}
}
