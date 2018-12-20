window.onload = function() {
    tael = document.getElementsByTagName('textarea');
    for (i = 0; i < tael.length; i++) {
        if (tael[i].className.indexOf('markdown_preview') >= 0) {
            attach_showdown_preview(tael[i].id, 1);
        }
    }
}
