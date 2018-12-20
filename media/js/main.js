$(document).ready(function() {
  $(window).on("scroll", function() {
    $(".navbar").toggleClass("compressed", $(window).scrollTop() >= 20);
  });
});

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


/*
 * Debian/Ubuntu download dropdowns
 */
function updateDebianSeries(select) {
    var deb = document.getElementById('series-deb');
    deb.innerHTML = select.value;
}
