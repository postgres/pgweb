/*
 * Initialize google tag manager for analytics integration
 */
var DNT = navigator.doNotTrack || window.doNotTrack || navigator.msDoNotTrack || window.msDoNotTrack;
if ((DNT != "1") && (DNT != "yes")) {
    (function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
    new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
    j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
    'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
    })(window,document,'script','dataLayer','GTM-WC97NKC');
}

/*
 * Fix scrolling of anchor links
 */
var shiftWindow = function() { scrollBy(0, -80) };
if (location.hash) shiftWindow();
window.addEventListener("hashchange", shiftWindow);


/* Copy a script from an HTML element to the clipboard,
 * removing comments and blank lines.
 * Arguments:
 *   trigger: The button calling the function, whose label will be updated
 *   elem: The element containing the script to copy
 */

function copyScript(trigger, elem) {
    var raw = document.getElementById(elem).innerHTML;

    // Create a scratch div to copy from
    var scratch = document.createElement("div");
    document.body.appendChild(scratch);

    // Copy the contents of the script box into the scratch div, removing
    // comments and blank lines
    var lines = raw.split("\n");
    var output = '';
    for (var l = 0; l < lines.length; l++) {
        if (lines[l][0] != '#' && lines[l].trim() != '')
            output += lines[l] + '<br />';
    }
    scratch.innerHTML = output.trim();

    // Perform the copy
    if(document.body.createTextRange) {
        // IE 11
        var range = document.body.createTextRange();
        range.moveToElementText(scratch);
        range.select();
        document.execCommand("Copy");
        document.getSelection().removeAllRanges()
    }
    else if(window.getSelection) {
        // Sane browsers
        var selection = window.getSelection();
        var range = document.createRange();
        range.selectNodeContents(scratch);
        selection.removeAllRanges();
        selection.addRange(range);
        document.execCommand("Copy");
        selection.removeAllRanges();
    }

    // Remove the scratch div
    scratch.parentNode.removeChild(scratch);

    // Indicate to the user that the script was copied
    var label = trigger.innerHTML;
    trigger.innerHTML = 'Copied!';

    setTimeout(function() {
        trigger.innerHTML = label;
    }, 3000);
}

/*
 * showDistros shows / hides the individual distributions of particular OS
 * families on the Download page
 */
function showDistros(btn, osDiv) {
    // Disable everything
    document.getElementById('btn-download-bsd').classList.remove("btn-download-active");;
    document.getElementById('download-subnav-bsd').style.display = 'none';
    document.getElementById('btn-download-linux').classList.remove("btn-download-active");
    document.getElementById('download-subnav-linux').style.display = 'none';

    // Enable the one we want
    btn.classList.add("btn-download-active");
    document.getElementById(osDiv).style.display = 'block';
}


/*
 * Register a confirm handler for forms that, well, requires confirmation
 * for someting.
 */
document.querySelectorAll('button[data-confirm]').forEach((button) => {
    button.addEventListener('click', (event) => {
        if (confirm(event.target.dataset.confirm)) {
            return true;
        }
        event.preventDefault();
        return false;
    });
});


/*
 * Theme switching
 */
function theme_apply() {
  'use strict';
  if (theme === 'light') {
    document.getElementById('btn-theme').innerHTML = '<i class="fas fa-moon"></i>';
    document.documentElement.setAttribute('data-theme', 'light');
    localStorage.setItem('theme', 'light');
  } else {
    document.getElementById('btn-theme').innerHTML = '<i class="fas fa-lightbulb"></i>';
    document.documentElement.setAttribute('data-theme', 'dark');
    localStorage.setItem('theme', 'dark');
  }
}

theme_apply();
document.getElementById("form-theme").style.display="block";

function theme_switch() {
  'use strict';
  if (theme === 'light') {
    theme = 'dark';
  } else {
    theme = 'light';
  }
  theme_apply();
}

let theme_OS = window.matchMedia('(prefers-color-scheme: light)');
theme_OS.addEventListener('change', function (e) {
  'use strict';
  if (e.matches) {
    theme = 'light';
  } else {
    theme = 'dark';
  }
  theme_apply();
});

