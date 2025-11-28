/*
 * Moderation preview handler
 * Renders HTML content in iframes to isolate styles from the main page
 */
document.addEventListener('DOMContentLoaded', function() {
    /* Find preview data textareas and render them in iframes */
    var dataAreas = document.getElementsByClassName('moderation-preview-data');
    for (var i = 0; i < dataAreas.length; i++) {
        var dataArea = dataAreas[i];
        var container = dataArea.parentElement;
        var content = dataArea.value;

        /* Create an iframe to isolate the HTML content styles */
        var iframe = document.createElement('iframe');
        iframe.className = 'moderation-preview-iframe';
        iframe.sandbox = 'allow-same-origin';
        iframe.srcdoc = content;

        /* Resize iframe to fit content after it loads */
        iframe.onload = function() {
            try {
                var contentHeight = this.contentDocument.body.scrollHeight;
                if (contentHeight > 0) {
                    this.style.height = (contentHeight + 20) + 'px';
                }
            } catch (e) {
                /* Only ignore SecurityError/cross-origin errors, rethrow others */
                if (e.name !== 'SecurityError') {
                    throw e;
                }
            }
        };

        container.appendChild(iframe);
    }
});
