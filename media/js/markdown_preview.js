// Functions to generate markdown previews for form fields

function attach_markdown_preview(objid, admin) {
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

    obj.infospan_html_base = admin ? '' : 'This field supports <a href="/account/markdown_submission/" target="_blank" rel="noopener">markdown</a>. See below for a preview.';

    obj.infospan = document.createElement('span');
    obj.infospan.innerHTML = obj.infospan_html_base;
    obj.parentNode.insertBefore(obj.infospan, newdiv);

    /* First force one update to happen right away */
    _do_update_markdown(obj);

    obj.addEventListener('keyup', function(e) {
        update_markdown(this);
    });
}

var __update_queue = {};
var __interval_setup = false;
function update_markdown(obj) {
    if (!__interval_setup) {
        __interval_setup = true;

        /* Global interval ticker running the update queue */
        setInterval(function() {
            /* This is where we actually update things */
            for (var id in __update_queue) {
                /* First remove it from the queue, so we can absorb another request while we run */
                delete __update_queue[id];
                obj = document.getElementById(id);

                _do_update_markdown(obj);
            }
        }, 2000); /* Maximum update interval is 2 seconds */
    }

    if (obj.value == obj.preview_div.value)
        return;

    /* Just flag that this needs to be done, and the ticker will pick it up */
    __update_queue[obj.id] = true;
}


function _do_update_markdown(obj) {
    if (obj.value == '') {
        /* Short-circuit the empty field case */
        obj.preview_div.innerHTML = '';
        return;
    }

    fetch('/account/mdpreview/', {
        method: 'POST',
        body: obj.value,
        headers: {
            'x-preview': 'md',
        },
        credentials: 'same-origin', /* for older browsers */
    }).then(function(response) {
        if (response.ok) {
            return response.text().then(function(text) {
                obj.preview_div.innerHTML = text;
            });
        } else {
            console.warn('md preview failed');
        }
    });
}
