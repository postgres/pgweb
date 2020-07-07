/* Event handlers */
function setupHandlers() {
    document.getElementById('copy-btn').addEventListener('click', function () {
        copyScript(this, 'script-box');
    });
}

document.addEventListener("DOMContentLoaded", setupHandlers);