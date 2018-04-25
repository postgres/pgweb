$(document).ready(function() {
  $(window).on("scroll", function() {
    $(".navbar").toggleClass("compressed", $(window).scrollTop() >= 20);
  });
});
