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
	newdiv.className = 'markdownpreview col-lg-12';

	if (admin) {
		obj.style.cssFloat = 'left';
		obj.style.marginRight = '10px';
		obj.style.width = newdiv.style.width = "400px";
		obj.style.height = newdiv.style.height = "200px";
		newdiv.className = newdiv.className + ' adminmarkdownpreview';
	}

	obj.preview_div = newdiv;

	obj.parentNode.insertBefore(newdiv, obj.nextSibling);

	obj.infospan_html_base = admin ? '' : 'This field supports <a href="http://daringfireball.net/projects/markdown/basics" target="_blank">markdown</a>. See below for a preview.';

	obj.infospan = document.createElement('span');
	obj.infospan.innerHTML = obj.infospan_html_base;
	obj.parentNode.insertBefore(obj.infospan, newdiv);

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

/*
 * Use regexp to do trivial HTML cleaning. The actual cleaning will happen
 * serverside later, so it doesn't matter that the regexps are far from
 * perfect - it should just be enough to alert the user that he/she is
 * using invalid markup.
 */
var _update_markdown_reopen = new RegExp("<([^\s/][^>]*)>", "g");
var _update_markdown_reclose = new RegExp("</([^>]+)>", "g");
function update_markdown(src, dest) {
	if (src.value != src.lastvalue) {
		src.lastvalue = src.value;
		if (_update_markdown_reclose.test(src.value) || _update_markdown_reopen.test(src.value)) {
		    dest.innerHTML = converter.makeHtml(src.value.replace(_update_markdown_reopen, '[HTML REMOVED]').replace(_update_markdown_reclose,'[HTML REMOVED2]'));
		    if (!src.last_had_html) {
			src.last_had_html = true;
			src.infospan.innerHTML = src.infospan_html_base + '<br/><span style="color: red;">You seem to be using HTML in your input - this will be filtered. Please use markdown instead!</span>';
		    }
		}
		else {
		    dest.innerHTML = converter.makeHtml(src.value);
		    if (src.last_had_html) {
			src.last_had_html = false;
			src.infospan.innerHTML = src.infospan_html_base;
		    }
		}
	}
}
