window.onload = function() {
    /* Preview in the pure admin views */
    let tael = document.getElementsByTagName('textarea');
    for (let i = 0; i < tael.length; i++) {
        if (tael[i].className.indexOf('markdown_preview') >= 0) {
            attach_showdown_preview(tael[i].id, 1);
        }
    }

    /* Preview in the moderation view */
    let previews = document.getElementsByClassName('mdpreview');
    for (let i = 0; i < previews.length; i++) {
        let iframe = previews[i];
        let textdiv = iframe.parentElement.previousElementSibling.getElementsByClassName('txtpreview')[0]
        let hiddendiv = iframe.nextElementSibling;

        /* Copy the HTML into the iframe */
        iframe.srcdoc = hiddendiv.innerHTML;

        /* Resize the height to to be the same */
        if (textdiv.offsetHeight > iframe.offsetHeight)
            iframe.style.height = textdiv.offsetHeight + 'px';
        if (iframe.offsetHeight > textdiv.offsetHeight)
            textdiv.style.height = iframe.offsetHeight + 'px';
    }
}
