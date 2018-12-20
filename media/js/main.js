$(document).ready(function() {
  $(window).on("scroll", function() {
    $(".navbar").toggleClass("compressed", $(window).scrollTop() >= 20);
  });
});


/*
 * Debian/Ubuntu download dropdowns
 */
function updateDebianSeries(select) {
    var deb = document.getElementById('series-deb');
    deb.innerHTML = select.value;
}
