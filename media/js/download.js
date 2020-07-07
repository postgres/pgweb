/* Event handlers */
function setupHandlers() {
    document.getElementById('btn-download-bsd').addEventListener('click', function (event) {
        showDistros(this, 'download-subnav-bsd');
        event.preventDefault();
    });

    document.getElementById('btn-download-linux').addEventListener('click', function (event) {
        showDistros(this, 'download-subnav-linux');
        event.preventDefault();
    });
}

document.addEventListener("DOMContentLoaded", setupHandlers);