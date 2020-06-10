/*
 * Initialize google analytics
 */
var _gaq = _gaq || [];
_gaq.push(['_setAccount', 'UA-1345454-1']);
_gaq.push(['_trackPageview']);
(function() {
    var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
    ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
    var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
})();

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
