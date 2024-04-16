/* Event handlers */
function setupHandlers() {
    /* BSD button on /download */
    if (document.getElementById("btn-download-bsd")) {
        document.getElementById('btn-download-bsd').addEventListener('click', function (event) {
            showDistros(this, 'download-subnav-bsd');
            event.preventDefault();
        });
    }

    /* Linux button on /download */
    if (document.getElementById("btn-download-linux")) {
        document.getElementById('btn-download-linux').addEventListener('click', function (event) {
            showDistros(this, 'download-subnav-linux');
            event.preventDefault();
        });
    }

    /* Copy Script buttons on /download/linux/debian and /download/linux/ubuntu */
    if (document.getElementById("copy-btn") && document.getElementById("script-box")) {
        document.getElementById('copy-btn').addEventListener('click', function () {
            copyScript(this, 'script-box');
        });
    }
    if (document.getElementById("copy-btn2") && document.getElementById("script-box2")) {
        document.getElementById('copy-btn2').addEventListener('click', function () {
            copyScript(this, 'script-box2');
        });
    }
}

document.addEventListener("DOMContentLoaded", setupHandlers);
